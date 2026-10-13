from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.baskets.models import BasketTemplate, BasketTemplateItem
from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.customers.models import Customer, CustomerStatus
from app.inventory.service import check_reservable
from app.payments.service import get_total_paid
from app.products.models import BaseUnit, Product
from app.sales.models import (
    Sale,
    SaleBasket,
    SaleBasketItem,
    SaleCancellationInspection,
    SaleCompositionHistory,
    SaleDeliveryHistory,
    SaleReopenHistory,
    SaleStockReservation,
    SaleStatus,
)
from app.sales.schemas import (
    SaleBasketAdd,
    SaleBasketCompositionUpdate,
    SaleBasketItemInput,
    SaleBasketUpdate,
    SaleCreate,
    SaleDeliveryPayload,
    SaleReopenPayload,
)


def _validate_quantity(product: Product, quantity: Decimal) -> None:
    if not quantity.is_finite() or quantity <= 0:
        raise BusinessRuleError("A quantidade deve ser maior que zero.")
    if product.base_unit == BaseUnit.UN and quantity != quantity.to_integral_value():
        raise BusinessRuleError("As quantidades para UN devem ser números inteiros.")


def _sale_or_raise(db: Session, sale_id: int, *, lock: bool = False) -> Sale:
    stmt = (
        select(Sale)
        .where(Sale.id == sale_id)
        .options(
            selectinload(Sale.customer),
            selectinload(Sale.baskets)
            .selectinload(SaleBasket.items)
            .selectinload(SaleBasketItem.product),
            selectinload(Sale.baskets).selectinload(SaleBasket.composition_histories),
            selectinload(Sale.baskets).selectinload(SaleBasket.delivery_histories),
            selectinload(Sale.reopen_histories),
        )
    )
    if lock:
        stmt = stmt.with_for_update()
    sale = db.scalar(stmt)
    if sale is None:
        raise ResourceNotFoundError("Venda não encontrada.")
    return sale


def _basket_or_raise(
    sale: Sale, basket_id: int
) -> SaleBasket:
    for basket in sale.baskets:
        if basket.id == basket_id:
            return basket
    raise ResourceNotFoundError("Cesta não encontrada na venda.")


def _template_or_raise(db: Session, template_id: int) -> BasketTemplate:
    template = db.scalar(
        select(BasketTemplate)
        .where(BasketTemplate.id == template_id)
        .options(
            selectinload(BasketTemplate.items).selectinload(BasketTemplateItem.product)
        )
    )
    if template is None:
        raise ResourceNotFoundError("Template de cesta não encontrado.")
    return template


def _customer_or_raise(db: Session, customer_id: int) -> Customer:
    customer = db.scalar(select(Customer).where(Customer.id == customer_id))
    if customer is None:
        raise ResourceNotFoundError("Cliente não encontrado.")
    return customer


def _normalized_items(
    db: Session, items: list[SaleBasketItemInput]
) -> list[tuple[Product, Decimal]]:
    totals: dict[int, tuple[Product, Decimal]] = {}
    product_ids = sorted({item.product_id for item in items})
    products = {
        product.id: product
        for product in db.scalars(
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        ).all()
    } if product_ids else {}

    for item in items:
        product = products.get(item.product_id)
        if product is None:
            raise ResourceNotFoundError("Produto não encontrado.")
        if not product.active:
            raise BusinessRuleError("Produtos inativos não podem ser incluídos.")
        _validate_quantity(product, item.quantity)
        previous = totals.get(product.id)
        quantity = item.quantity + (previous[1] if previous else Decimal(0))
        _validate_quantity(product, quantity)
        totals[product.id] = (product, quantity)

    return list(totals.values())


def create_sale(db: Session, payload: SaleCreate) -> Sale:
    customer = _customer_or_raise(db, payload.customer_id)
    if customer.status != CustomerStatus.ACTIVE.value:
        raise BusinessRuleError("Apenas clientes ativos podem originar novas vendas.")

    if not payload.baskets:
        raise BusinessRuleError("A venda deve conter ao menos uma cesta.")

    sale = Sale(
        customer_id=customer.id,
        status=SaleStatus.RASCUNHO.value,
        total=Decimal("0.00"),
    )
    db.add(sale)
    db.flush()

    total = Decimal("0.00")
    for basket_in in payload.baskets:
        template = _template_or_raise(db, basket_in.template_id)
        if template.price is None:
            raise BusinessRuleError(
                "A cesta de origem não possui preço de venda definido."
            )

        price = basket_in.price if basket_in.price is not None else template.price
        sale_basket = SaleBasket(
            sale_id=sale.id,
            name=template.name,
            origin_template_id=template.id,
            price=price,
            recipient_name=basket_in.recipient_name,
            delivery_address=basket_in.delivery_address,
            delivery_date=basket_in.delivery_date,
            delivery_time=basket_in.delivery_time,
            is_prepared=False,
            is_delivered=False,
        )
        db.add(sale_basket)
        db.flush()

        # Copy items from template
        for t_item in template.items:
            sale_item = SaleBasketItem(
                sale_basket_id=sale_basket.id,
                product_id=t_item.product_id,
                quantity=t_item.quantity,
            )
            db.add(sale_item)

        total += price

    sale.total = total
    db.commit()
    return _sale_or_raise(db, sale.id)


def add_basket_to_sale(
    db: Session, sale_id: int, payload: SaleBasketAdd
) -> SaleBasket:
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.RASCUNHO.value:
        raise BusinessRuleError(
            "Cestas só podem ser adicionadas enquanto a venda estiver em rascunho."
        )

    template = _template_or_raise(db, payload.template_id)
    if template.price is None:
        raise BusinessRuleError(
            "A cesta de origem não possui preço de venda definido."
        )

    price = payload.price if payload.price is not None else template.price
    sale_basket = SaleBasket(
        sale_id=sale.id,
        name=template.name,
        origin_template_id=template.id,
        price=price,
        recipient_name=payload.recipient_name,
        delivery_address=payload.delivery_address,
        delivery_date=payload.delivery_date,
        delivery_time=payload.delivery_time,
        is_prepared=False,
        is_delivered=False,
    )
    db.add(sale_basket)
    db.flush()

    for t_item in template.items:
        sale_item = SaleBasketItem(
            sale_basket_id=sale_basket.id,
            product_id=t_item.product_id,
            quantity=t_item.quantity,
        )
        db.add(sale_item)

    # Recalculate total
    sale.total = sum((b.price for b in sale.baskets), Decimal("0.00")) + price
    db.commit()
    return _basket_or_raise(_sale_or_raise(db, sale.id), sale_basket.id)


def remove_basket_from_sale(
    db: Session, sale_id: int, basket_id: int
) -> None:
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.RASCUNHO.value:
        raise BusinessRuleError(
            "Cestas só podem ser removidas enquanto a venda estiver em rascunho."
        )

    if len(sale.baskets) <= 1:
        raise BusinessRuleError("A venda deve conter ao menos uma cesta.")

    basket = _basket_or_raise(sale, basket_id)
    db.delete(basket)
    db.flush()

    sale.total = sum(
        (b.price for b in sale.baskets if b.id != basket_id), Decimal("0.00")
    )
    db.commit()


def update_basket_delivery(
    db: Session, sale_id: int, basket_id: int, payload: SaleBasketUpdate
) -> SaleBasket:
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status in (SaleStatus.ENTREGUE.value, SaleStatus.CANCELADA.value):
        raise BusinessRuleError(
            "Não é permitido alterar dados de entrega em vendas entregues ou canceladas."
        )

    basket = _basket_or_raise(sale, basket_id)
    if payload.recipient_name is not None:
        basket.recipient_name = payload.recipient_name.strip() or None
    if payload.delivery_address is not None:
        basket.delivery_address = payload.delivery_address.strip() or None
    if payload.delivery_date is not None:
        basket.delivery_date = payload.delivery_date
    if payload.delivery_time is not None:
        basket.delivery_time = payload.delivery_time.strip() or None

    db.commit()
    return _basket_or_raise(_sale_or_raise(db, sale.id), basket_id)


def update_basket_price(
    db: Session, sale_id: int, basket_id: int, price: Decimal
) -> SaleBasket:
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.RASCUNHO.value:
        raise BusinessRuleError(
            "O preço da cesta não pode ser alterado após a confirmação da venda."
        )

    basket = _basket_or_raise(sale, basket_id)
    basket.price = price
    db.flush()

    sale.total = sum(
        (b.price if b.id != basket_id else price for b in sale.baskets),
        Decimal("0.00"),
    )
    db.commit()
    return _basket_or_raise(_sale_or_raise(db, sale.id), basket_id)


def update_basket_composition(
    db: Session,
    sale_id: int,
    basket_id: int,
    payload: SaleBasketCompositionUpdate,
) -> SaleBasket:
    """Composition change with reservation (Flow 4, RES-006, RES-007).
    
    For confirmed/preparing sales, computes quantity differences and updates reservations.
    """
    from app.inventory.service import check_reservable, get_active_reservations_for_product, _balance

    sale = _sale_or_raise(db, sale_id, lock=True)

    if sale.status in (SaleStatus.ENTREGUE.value, SaleStatus.CANCELADA.value):
        raise BusinessRuleError(
            "Não é permitido alterar composição em vendas entregues ou canceladas."
        )

    if sale.status == SaleStatus.PRONTA.value:
        raise BusinessRuleError(
            "Não é permitido alterar composição diretamente em venda pronta. É necessário reabrir a venda."
        )

    if sale.status == SaleStatus.EM_PREPARACAO.value:
        if not payload.confirmed_warning:
            raise BusinessRuleError(
                "É necessário confirmar que itens podem já ter sido separados ou preparados."
            )

    operator_name = payload.operator_name.strip()
    if sale.status in (SaleStatus.CONFIRMADA.value, SaleStatus.EM_PREPARACAO.value):
        if not operator_name:
            raise BusinessRuleError(
                "A identificação textual do operador é obrigatória."
            )

    basket = _basket_or_raise(sale, basket_id)

    # Compute old product→quantity map from current basket items
    old_quantities: dict[int, Decimal] = {}
    for item in basket.items:
        old_quantities[item.product_id] = (
            old_quantities.get(item.product_id, Decimal(0)) + item.quantity
        )

    normalized = _normalized_items(db, payload.items)

    # Compute new product→quantity map
    new_quantities: dict[int, Decimal] = {}
    for product, quantity in normalized:
        new_quantities[product.id] = new_quantities.get(product.id, Decimal(0)) + quantity

    # If sale is confirmed or preparing, handle reservation changes
    if sale.status in (SaleStatus.CONFIRMADA.value, SaleStatus.EM_PREPARACAO.value):
        # Lock all reservation rows for this sale
        reservations = {
            res.product_id: res
            for res in db.scalars(
                select(SaleStockReservation)
                .where(SaleStockReservation.sale_id == sale.id)
                .with_for_update()
            ).all()
        }

        # Identify all affected products
        all_product_ids = sorted(set(list(old_quantities.keys()) + list(new_quantities.keys())))

        # Lock all affected product rows (sorted)
        if all_product_ids:
            products = {
                product.id: product
                for product in db.scalars(
                    select(Product)
                    .where(Product.id.in_(all_product_ids))
                    .order_by(Product.id)
                    .with_for_update()
                ).all()
            }
        else:
            products = {}

        # Check all increases first before applying any changes
        for product_id in all_product_ids:
            old_qty = old_quantities.get(product_id, Decimal(0))
            new_qty = new_quantities.get(product_id, Decimal(0))
            if new_qty > old_qty:
                difference = new_qty - old_qty
                reservation = reservations.get(product_id)
                if reservation is None:
                    # New product — need to check reservable
                    if not check_reservable(db, product_id, difference):
                        product = products.get(product_id)
                        product_name = product.name if product else f"ID {product_id}"
                        raise BusinessRuleError(
                            f"Estoque insuficiente para adicionar {product_name}. "
                            f"Diferença necessária: {difference}."
                        )
                else:
                    # Existing product — check if enough available for the difference
                    active_res = get_active_reservations_for_product(db, product_id)
                    current_bal = _balance(db, product_id)
                    available = current_bal - active_res
                    if available < difference:
                        product = products.get(product_id)
                        product_name = product.name if product else f"ID {product_id}"
                        raise BusinessRuleError(
                            f"Estoque insuficiente para aumentar {product_name}. "
                            f"Diferença necessária: {difference}, disponível: {available}."
                        )

        # Apply reservation changes
        for product_id in all_product_ids:
            old_qty = old_quantities.get(product_id, Decimal(0))
            new_qty = new_quantities.get(product_id, Decimal(0))
            reservation = reservations.get(product_id)

            if new_qty > old_qty:
                difference = new_qty - old_qty
                if reservation is None:
                    # New product — create reservation
                    new_reservation = SaleStockReservation(
                        sale_id=sale.id,
                        product_id=product_id,
                        current_quantity=new_qty,
                        reserved_quantity=new_qty,
                        consumed_quantity=Decimal(0),
                        status='ACTIVE',
                    )
                    db.add(new_reservation)
                else:
                    # Increase — reserve the difference
                    reservation.reserved_quantity += difference
                    reservation.current_quantity = new_qty

            elif new_qty < old_qty and reservation is not None:
                difference = old_qty - new_qty
                unconsumed = reservation.reserved_quantity - reservation.consumed_quantity
                release_amount = min(difference, unconsumed)
                reservation.reserved_quantity -= release_amount
                reservation.current_quantity = new_qty
                if reservation.reserved_quantity == reservation.consumed_quantity:
                    if new_qty == 0:
                        reservation.status = 'RELEASED'
                    else:
                        reservation.status = 'ACTIVE'

            elif new_qty == 0 and reservation is not None:
                # Product removed entirely
                unconsumed = reservation.reserved_quantity - reservation.consumed_quantity
                release_amount = min(old_qty, unconsumed)
                reservation.reserved_quantity -= release_amount
                reservation.current_quantity = Decimal(0)
                if reservation.reserved_quantity == reservation.consumed_quantity:
                    reservation.status = 'RELEASED'

    # Snapshot previous items
    previous_snapshot = [
        {
            "product_id": it.product_id,
            "product_name": it.product.name,
            "quantity": str(it.quantity),
            "unit": it.product.base_unit.value if hasattr(it.product.base_unit, "value") else str(it.product.base_unit),
        }
        for it in basket.items
    ]

    # Clear and replace items
    basket.items.clear()
    db.flush()

    for product, quantity in normalized:
        item = SaleBasketItem(
            sale_basket_id=basket.id,
            product_id=product.id,
            quantity=quantity,
        )
        db.add(item)
    db.flush()

    new_snapshot = [
        {
            "product_id": product.id,
            "product_name": product.name,
            "quantity": str(quantity),
            "unit": product.base_unit.value if hasattr(product.base_unit, "value") else str(product.base_unit),
        }
        for product, quantity in normalized
    ]

    # Save history if operator is given or if in CONFIRMADA / EM_PREPARACAO
    if operator_name:
        history = SaleCompositionHistory(
            sale_basket_id=basket.id,
            previous_items=previous_snapshot,
            new_items=new_snapshot,
            operator_name=operator_name,
        )
        db.add(history)

    # If in EM_PREPARACAO, invalidate preparation of THIS basket
    if sale.status == SaleStatus.EM_PREPARACAO.value:
        basket.is_prepared = False

    # Note: price and total remain untouched!
    db.commit()
    return _basket_or_raise(_sale_or_raise(db, sale.id), basket_id)


def confirm_sale(db: Session, sale_id: int) -> Sale:
    """Financial confirmation + full reservation (Flow 2, RES-001, RES-002).
    
    Steps:
    1. Lock sale.
    2. Validate RASCUNHO + delivery data.
    3. Validate payment ≥ 50% of sale total.
    4. Aggregate products × quantities across all baskets.
    5. Lock all products (sorted by product_id).
    6. For each product: check reservable, then INSERT reservation.
    7. UPDATE sale.status = CONFIRMADA.
    8. COMMIT.
    """
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.RASCUNHO.value:
        raise BusinessRuleError(
            f"Apenas vendas em rascunho podem ser confirmadas (status atual: {sale.status})."
        )

    # Validate delivery data on all baskets
    for basket in sale.baskets:
        if not basket.recipient_name or not basket.recipient_name.strip():
            raise BusinessRuleError(
                "Todas as cestas devem possuir destinatário, endereço, data e horário de entrega preenchidos para confirmação."
            )
        if not basket.delivery_address or not basket.delivery_address.strip():
            raise BusinessRuleError(
                "Todas as cestas devem possuir destinatário, endereço, data e horário de entrega preenchidos para confirmação."
            )
        if not basket.delivery_date:
            raise BusinessRuleError(
                "Todas as cestas devem possuir destinatário, endereço, data e horário de entrega preenchidos para confirmação."
            )
        if not basket.delivery_time or not basket.delivery_time.strip():
            raise BusinessRuleError(
                "Todas as cestas devem possuir destinatário, endereço, data e horário de entrega preenchidos para confirmação."
            )

    # Validate payment ≥ 50% of sale total
    total_paid = get_total_paid(db, sale_id)
    if sale.total > 0:
        payment_percentage = total_paid / sale.total * 100
        if payment_percentage < 50:
            raise BusinessRuleError(
                f"Pagamento insuficiente para confirmação. "
                f"Total pago: R${total_paid:.2f} ({payment_percentage:.1f}% de R${sale.total:.2f}). "
                f"Mínimo requerido: 50%."
            )

    # Aggregate products × quantities across all baskets
    product_quantities: dict[int, Decimal] = {}
    for basket in sale.baskets:
        for item in basket.items:
            product_quantities[item.product_id] = (
                product_quantities.get(item.product_id, Decimal(0)) + item.quantity
            )

    # Sort by product_id for consistent lock ordering
    sorted_product_ids = sorted(product_quantities.keys())

    # Lock all products first (sorted by product_id)
    products = {
        product.id: product
        for product in db.scalars(
            select(Product)
            .where(Product.id.in_(sorted_product_ids))
            .order_by(Product.id)
            .with_for_update()
        ).all()
    }

    # Check reservable for each product
    shortages: list[str] = []
    for product_id in sorted_product_ids:
        quantity_needed = product_quantities[product_id]
        product = products[product_id]
        if not check_reservable(db, product_id, quantity_needed):
            shortages.append(
                f"{product.name}: necessário {quantity_needed} {product.base_unit}"
            )

    if shortages:
        raise BusinessRuleError(
            "Estoque insuficiente para confirmação. Produtos faltantes: "
            + "; ".join(shortages)
        )

    # Create reservation rows for each product
    for product_id in sorted_product_ids:
        quantity_needed = product_quantities[product_id]
        reservation = SaleStockReservation(
            sale_id=sale.id,
            product_id=product_id,
            current_quantity=quantity_needed,
            reserved_quantity=quantity_needed,
            consumed_quantity=Decimal(0),
            status='ACTIVE',
        )
        db.add(reservation)

    # Update sale status
    sale.status = SaleStatus.CONFIRMADA.value
    db.commit()
    return _sale_or_raise(db, sale.id)


def start_preparation(db: Session, sale_id: int) -> Sale:
    """Physical deduction at preparation start (Flow 3, RES-005).
    
    Steps:
    1. Lock sale.
    2. Validate CONFIRMADA.
    3. Lock all reservation rows.
    4. Lock all product rows (sorted).
    5. For each reservation: compute to_deduct, check balance, create OUTPUT, update consumed.
    6. UPDATE sale.status = EM_PREPARAÇÃO.
    7. COMMIT.
    """
    from app.inventory.service import create_movement
    from app.products.models import MovementType

    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.CONFIRMADA.value:
        raise BusinessRuleError(
            f"Não é possível iniciar preparação a partir do estado {sale.status}."
        )

    # Lock all reservation rows for this sale
    reservations = list(
        db.scalars(
            select(SaleStockReservation)
            .where(SaleStockReservation.sale_id == sale.id)
            .order_by(SaleStockReservation.product_id)
            .with_for_update()
        ).all()
    )

    # Collect and lock all product rows (sorted by product_id)
    product_ids = sorted({res.product_id for res in reservations})
    products = {
        product.id: product
        for product in db.scalars(
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        ).all()
    }

    # For each reservation: compute to_deduct, check balance, create OUTPUT, update consumed
    for reservation in reservations:
        to_deduct = reservation.reserved_quantity - reservation.consumed_quantity
        if to_deduct > 0:
            from app.inventory.service import _balance
            current_balance = _balance(db, reservation.product_id)
            if current_balance < to_deduct:
                product = products[reservation.product_id]
                raise BusinessRuleError(
                    f"Estoque insuficiente para iniciar preparação. "
                    f"{product.name}: disponível {current_balance} {product.base_unit}, "
                    f"necessário {to_deduct} {product.base_unit}."
                )
            # Create OUTPUT movement
            create_movement(
                db,
                product_id=reservation.product_id,
                quantity=-to_deduct,
                movement_type=MovementType.OUTPUT,
                sale_id=sale.id,
                use_savepoint=False,
            )
            # Update consumed quantity
            reservation.consumed_quantity += to_deduct
            if reservation.consumed_quantity == reservation.reserved_quantity:
                reservation.status = 'CONSUMED'

    sale.status = SaleStatus.EM_PREPARACAO.value
    db.commit()
    return _sale_or_raise(db, sale.id)


def mark_basket_prepared(
    db: Session, sale_id: int, basket_id: int
) -> SaleBasket:
    """Additional deduction on basket preparation (Flow 5, RES-006).
    
    For baskets with composition changes after prep start, deducts additional quantities.
    """
    from app.inventory.service import create_movement, _balance
    from app.products.models import MovementType

    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.EM_PREPARACAO.value:
        raise BusinessRuleError(
            "A preparação de cestas só pode ser registrada quando a venda estiver em preparação."
        )

    basket = _basket_or_raise(sale, basket_id)

    # Early return if already prepared (idempotency)
    if basket.is_prepared:
        return _basket_or_raise(_sale_or_raise(db, sale.id), basket_id)

    # For each product in this basket, collect quantities
    basket_product_quantities: dict[int, Decimal] = {}
    for item in basket.items:
        basket_product_quantities[item.product_id] = (
            basket_product_quantities.get(item.product_id, Decimal(0)) + item.quantity
        )

    # Lock all reservation rows for this sale
    reservations = {
        res.product_id: res
        for res in db.scalars(
            select(SaleStockReservation)
            .where(SaleStockReservation.sale_id == sale.id)
            .with_for_update()
        ).all()
    }

    # Lock all affected product rows (sorted)
    product_ids = sorted(basket_product_quantities.keys())
    if product_ids:
        products = {
            product.id: product
            for product in db.scalars(
                select(Product)
                .where(Product.id.in_(product_ids))
                .order_by(Product.id)
                .with_for_update()
            ).all()
        }
    else:
        products = {}

    # For each product in this basket: deduct unconsumed portion
    for product_id in product_ids:
        reservation = reservations.get(product_id)
        if reservation is None:
            continue

        to_deduct = basket_product_quantities[product_id]
        actual_deduct = min(to_deduct, reservation.reserved_quantity - reservation.consumed_quantity)

        if actual_deduct > 0:
            current_balance = _balance(db, product_id)
            if current_balance < actual_deduct:
                product = products.get(product_id)
                product_name = product.name if product else f"ID {product_id}"
                raise BusinessRuleError(
                    f"Estoque insuficiente para marcar cesta preparada. "
                    f"{product_name}: disponível {current_balance}, necessário {actual_deduct}."
                )
            create_movement(
                db,
                product_id=product_id,
                quantity=-actual_deduct,
                movement_type=MovementType.OUTPUT,
                sale_id=sale.id,
                use_savepoint=False,
            )
            reservation.consumed_quantity += actual_deduct
            if reservation.consumed_quantity == reservation.reserved_quantity:
                reservation.status = 'CONSUMED'

    basket.is_prepared = True
    db.flush()

    # If all baskets are prepared, transition to PRONTA
    if all(b.is_prepared for b in sale.baskets):
        sale.status = SaleStatus.PRONTA.value

    db.commit()
    return _basket_or_raise(_sale_or_raise(db, sale.id), basket_id)


def reopen_sale(db: Session, sale_id: int, payload: SaleReopenPayload) -> Sale:
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.PRONTA.value:
        raise BusinessRuleError("Apenas vendas com status PRONTA podem ser reabertas.")

    reason = payload.reason.strip()
    if not reason:
        raise BusinessRuleError("A justificativa é obrigatória para reabrir a venda.")

    operator_name = payload.operator_name.strip()
    if not operator_name:
        raise BusinessRuleError("A identificação textual do operador é obrigatória.")

    history = SaleReopenHistory(
        sale_id=sale.id,
        reason=reason,
        operator_name=operator_name,
    )
    db.add(history)

    sale.status = SaleStatus.EM_PREPARACAO.value
    db.commit()
    return _sale_or_raise(db, sale.id)


def deliver_basket(
    db: Session, sale_id: int, basket_id: int, payload: SaleDeliveryPayload
) -> SaleBasket:
    sale = _sale_or_raise(db, sale_id, lock=True)

    basket = _basket_or_raise(sale, basket_id)

    # Idempotency check first: if basket is already delivered, return immediately
    # without validating sale status. This allows re-delivering a basket that was
    # the last one to complete the sale (status already ENTREGUE).
    if basket.is_delivered:
        return basket

    if sale.status in (SaleStatus.ENTREGUE.value, SaleStatus.CANCELADA.value):
        raise BusinessRuleError(
            "Não é possível registrar entrega em venda já entregue ou cancelada."
        )
    if sale.status == SaleStatus.RASCUNHO.value:
        raise BusinessRuleError(
            "Não é possível registrar entrega em venda em rascunho."
        )

    operator_name = payload.operator_name.strip()
    if not operator_name:
        raise BusinessRuleError("A identificação textual do operador é obrigatória.")

    if not basket.is_prepared:
        raise BusinessRuleError(
            "Não é possível registrar entrega de cesta que ainda não foi preparada."
        )

    basket.is_delivered = True

    history = SaleDeliveryHistory(
        sale_basket_id=basket.id,
        operator_name=operator_name,
    )
    db.add(history)
    db.flush()

    # If all baskets are delivered, transition to ENTREGUE
    if all(b.is_delivered for b in sale.baskets):
        sale.status = SaleStatus.ENTREGUE.value

    db.commit()
    return _basket_or_raise(_sale_or_raise(db, sale.id), basket_id)


def cancel_sale(db: Session, sale_id: int) -> Sale:
    """Cancel with reservation release and inspection (Flow 7/8, RES-010/011/012).
    
    Before prep: release all reservations (Flow 7).
    After prep: release unconsumed, create inspection records for consumed (Flow 8).
    """
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status in (SaleStatus.ENTREGUE.value, SaleStatus.CANCELADA.value):
        raise BusinessRuleError(
            "Vendas entregues ou canceladas não podem ser canceladas."
        )

    if any(b.is_delivered for b in sale.baskets):
        raise BusinessRuleError(
            "Não é permitido cancelar uma venda que possui entregas já realizadas."
        )

    # Lock all reservation rows for this sale
    reservations = list(
        db.scalars(
            select(SaleStockReservation)
            .where(SaleStockReservation.sale_id == sale.id)
            .with_for_update()
        ).all()
    )

    if sale.status in (SaleStatus.RASCUNHO.value, SaleStatus.CONFIRMADA.value):
        # Flow 7: Cancel before preparation — release all reservations
        for reservation in reservations:
            reservation.reserved_quantity = reservation.consumed_quantity
            reservation.status = 'RELEASED'
    elif sale.status in (SaleStatus.EM_PREPARACAO.value, SaleStatus.PRONTA.value):
        # Flow 8: Cancel after preparation
        for reservation in reservations:
            # Release unconsumed portion
            if reservation.consumed_quantity < reservation.reserved_quantity:
                reservation.reserved_quantity = reservation.consumed_quantity
                reservation.status = 'RELEASED'
            # Create inspection record for consumed products
            if reservation.consumed_quantity > 0:
                inspection = SaleCancellationInspection(
                    sale_id=sale.id,
                    product_id=reservation.product_id,
                    consumed_quantity=reservation.consumed_quantity,
                    inspected_quantity=Decimal(0),
                    reusable_quantity=Decimal(0),
                    operator_name='',
                    inspected_at=None,
                    reintegrated_quantity=Decimal(0),
                    reintegrated_movement_id=None,
                    status='PENDING',
                )
                db.add(inspection)

    sale.status = SaleStatus.CANCELADA.value
    db.commit()
    return _sale_or_raise(db, sale.id)


def get_sale(db: Session, sale_id: int) -> Sale:
    return _sale_or_raise(db, sale_id)


def record_inspection(
    db: Session,
    inspection_id: int,
    inspected_quantity: Decimal,
    reusable_quantity: Decimal,
    operator_name: str,
) -> SaleCancellationInspection:
    """Record inspection result (Flow 10, RES-011 step 2)."""
    from datetime import datetime as dt

    inspection = db.scalar(
        select(SaleCancellationInspection)
        .where(SaleCancellationInspection.id == inspection_id)
        .with_for_update()
    )
    if inspection is None:
        raise ResourceNotFoundError("Registro de inspeção não encontrado.")

    if inspection.status != 'PENDING':
        raise BusinessRuleError(
            f"Inspeção já registrada (status atual: {inspection.status})."
        )

    if inspected_quantity > inspection.consumed_quantity:
        raise BusinessRuleError(
            "A quantidade inspecionada não pode exceder a quantidade consumida."
        )

    if reusable_quantity > inspected_quantity:
        raise BusinessRuleError(
            "A quantidade reutilizável não pode exceder a quantidade inspecionada."
        )

    inspection.inspected_quantity = inspected_quantity
    inspection.reusable_quantity = reusable_quantity
    inspection.operator_name = operator_name
    inspection.inspected_at = datetime.now(tz=timezone.utc)
    if reusable_quantity == 0:
        inspection.status = 'DISCARDED'
    else:
        inspection.status = 'INSPECTED'

    db.commit()
    return inspection


def reintegrate_inspection(
    db: Session,
    inspection_id: int,
    quantity: Decimal,
) -> SaleCancellationInspection:
    """Reintegrate reusable products back to inventory (Flow 9, RES-011 step 3)."""
    from app.inventory.service import create_movement
    from app.products.models import MovementType

    inspection = db.scalar(
        select(SaleCancellationInspection)
        .where(SaleCancellationInspection.id == inspection_id)
        .with_for_update()
    )
    if inspection is None:
        raise ResourceNotFoundError("Registro de inspeção não encontrado.")

    if inspection.status != 'INSPECTED':
        raise BusinessRuleError(
            f"Inspeção não pode ser reintegrada (status atual: {inspection.status})."
        )

    if inspection.reintegrated_quantity >= inspection.reusable_quantity:
        raise BusinessRuleError(
            "Reintegração já concluída para este registro."
        )

    to_reintegrate = min(quantity, inspection.reusable_quantity - inspection.reintegrated_quantity)

    # Lock product row
    product = db.scalar(
        select(Product)
        .where(Product.id == inspection.product_id)
        .with_for_update()
    )
    if product is None:
        raise ResourceNotFoundError("Produto não encontrado.")

    # Create ENTRY movement
    movement = create_movement(
        db,
        product_id=inspection.product_id,
        quantity=to_reintegrate,
        movement_type=MovementType.ENTRY,
        sale_id=inspection.sale_id,
        use_savepoint=False,
    )

    # Update inspection
    inspection.reintegrated_quantity += to_reintegrate
    inspection.reintegrated_movement_id = movement.id
    if inspection.reintegrated_quantity == inspection.reusable_quantity:
        inspection.status = 'REINTEGRATED'

    db.commit()
    return inspection


def get_inspections_for_sale(db: Session, sale_id: int) -> list[SaleCancellationInspection]:
    """Get all inspection records for a canceled sale."""
    return list(
        db.scalars(
            select(SaleCancellationInspection)
            .where(SaleCancellationInspection.sale_id == sale_id)
            .order_by(SaleCancellationInspection.product_id)
        ).all()
    )


def list_sales(
    db: Session,
    status: str | None = None,
    customer_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Sale], int]:
    stmt = (
        select(Sale)
        .options(
            selectinload(Sale.customer),
            selectinload(Sale.baskets)
            .selectinload(SaleBasket.items)
            .selectinload(SaleBasketItem.product),
            selectinload(Sale.baskets).selectinload(SaleBasket.composition_histories),
            selectinload(Sale.baskets).selectinload(SaleBasket.delivery_histories),
            selectinload(Sale.reopen_histories),
        )
        .order_by(Sale.id.desc())
    )
    if status and status != "ALL":
        stmt = stmt.where(Sale.status == status)
    if customer_id is not None:
        stmt = stmt.where(Sale.customer_id == customer_id)

    # Count
    total = len(db.scalars(stmt).all())

    # Paginate
    items = db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
    return list(items), total
