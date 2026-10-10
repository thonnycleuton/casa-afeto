from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.baskets.models import BasketTemplate, BasketTemplateItem
from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.customers.models import Customer, CustomerStatus
from app.products.models import BaseUnit, Product
from app.sales.models import (
    Sale,
    SaleBasket,
    SaleBasketItem,
    SaleCompositionHistory,
    SaleDeliveryHistory,
    SaleReopenHistory,
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
    normalized = _normalized_items(db, payload.items)

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
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.RASCUNHO.value:
        raise BusinessRuleError(
            f"Apenas vendas em rascunho podem ser confirmadas (status atual: {sale.status})."
        )

    # Validate delivery data on all baskets (AC-M4-009)
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

    sale.status = SaleStatus.CONFIRMADA.value
    db.commit()
    return _sale_or_raise(db, sale.id)


def start_preparation(db: Session, sale_id: int) -> Sale:
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.CONFIRMADA.value:
        raise BusinessRuleError(
            f"Não é possível iniciar preparação a partir do estado {sale.status}."
        )

    sale.status = SaleStatus.EM_PREPARACAO.value
    db.commit()
    return _sale_or_raise(db, sale.id)


def mark_basket_prepared(
    db: Session, sale_id: int, basket_id: int
) -> SaleBasket:
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status != SaleStatus.EM_PREPARACAO.value:
        raise BusinessRuleError(
            "A preparação de cestas só pode ser registrada quando a venda estiver em preparação."
        )

    basket = _basket_or_raise(sale, basket_id)
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

    basket = _basket_or_raise(sale, basket_id)
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
    sale = _sale_or_raise(db, sale_id, lock=True)
    if sale.status in (SaleStatus.ENTREGUE.value, SaleStatus.CANCELADA.value):
        raise BusinessRuleError(
            "Vendas entregues ou canceladas não podem ser canceladas."
        )

    if any(b.is_delivered for b in sale.baskets):
        raise BusinessRuleError(
            "Não é permitido cancelar uma venda que possui entregas já realizadas."
        )

    sale.status = SaleStatus.CANCELADA.value
    db.commit()
    return _sale_or_raise(db, sale.id)


def get_sale(db: Session, sale_id: int) -> Sale:
    return _sale_or_raise(db, sale_id)


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
