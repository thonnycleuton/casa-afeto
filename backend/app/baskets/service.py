from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.inventory.service import product_balances
from app.products.models import BaseUnit, Product
from app.baskets.models import (
    BasketTemplate,
    BasketTemplateItem,
)
from app.baskets.schemas import (
    BasketItemInput,
    BasketTemplateRead,
    ProductCompositionRead,
)


def _validate_quantity(product: Product, quantity: Decimal) -> None:
    if not quantity.is_finite() or quantity <= 0:
        raise BusinessRuleError("A quantidade deve ser maior que zero.")
    if product.base_unit == BaseUnit.UN and quantity != quantity.to_integral_value():
        raise BusinessRuleError("As quantidades para UN devem ser números inteiros.")


def _product_or_raise(
    db: Session, product_id: int, *, lock: bool = False
) -> Product:
    statement = select(Product).where(Product.id == product_id)
    if lock:
        statement = statement.with_for_update().execution_options(
            populate_existing=True
        )
    product = db.scalar(statement)
    if product is None:
        raise ResourceNotFoundError("Produto não encontrado.")
    return product


def _template_or_raise(
    db: Session, template_id: int, *, lock: bool = False
) -> BasketTemplate:
    statement = (
        select(BasketTemplate)
        .where(BasketTemplate.id == template_id)
        .options(selectinload(BasketTemplate.items).selectinload(BasketTemplateItem.product))
    )
    if lock:
        statement = statement.with_for_update()
    template = db.scalar(statement)
    if template is None:
        raise ResourceNotFoundError("Template de cesta não encontrado.")
    return template


def _normalized_items(
    db: Session, items: list[BasketItemInput]
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


def _lock_template_products(
    db: Session, items: list[BasketTemplateItem]
) -> None:
    product_ids = sorted({item.product_id for item in items})
    products = db.scalars(
        select(Product)
        .where(Product.id.in_(product_ids))
        .order_by(Product.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()
    if len(products) != len(product_ids):
        raise ResourceNotFoundError("Produto não encontrado.")
    if any(not product.active for product in products):
        raise BusinessRuleError(
            "O template contém produto inativo e não pode originar cesta."
        )


def _touch(entity: BasketTemplate) -> None:
    entity.updated_at = datetime.now(timezone.utc)


def create_template(
    db: Session,
    name: str,
    items: list[BasketItemInput],
    price: Decimal | None = None,
) -> BasketTemplate:
    with db.begin():
        normalized_items = _normalized_items(db, items)
        template = BasketTemplate(name=name, price=price, active=True)
        db.add(template)
        db.flush()
        template.items = [
            BasketTemplateItem(product=product, quantity=quantity)
            for product, quantity in normalized_items
        ]
        db.flush()
        db.refresh(template)
    return template


def list_templates(db: Session) -> list[BasketTemplate]:
    return list(
        db.scalars(
            select(BasketTemplate)
            .options(
                selectinload(BasketTemplate.items).selectinload(
                    BasketTemplateItem.product
                )
            )
            .order_by(BasketTemplate.name, BasketTemplate.id)
        ).all()
    )


def get_template(db: Session, template_id: int) -> BasketTemplate:
    return _template_or_raise(db, template_id)


def update_template(
    db: Session,
    template_id: int,
    name: str | None = None,
    price: Decimal | None = None,
    update_price: bool = False,
) -> BasketTemplate:
    with db.begin():
        template = _template_or_raise(db, template_id, lock=True)
        if name is not None:
            template.name = name
        if update_price:
            template.price = price
        _touch(template)
        db.flush()
    return template


def set_template_active(
    db: Session, template_id: int, active: bool
) -> BasketTemplate:
    with db.begin():
        template = _template_or_raise(db, template_id, lock=True)
        template.active = active
        _touch(template)
        db.flush()
    return template


def add_template_item(
    db: Session, template_id: int, product_id: int, quantity: Decimal
) -> BasketTemplate:
    with db.begin():
        template = _template_or_raise(db, template_id, lock=True)
        product = _product_or_raise(db, product_id, lock=True)
        if not product.active:
            raise BusinessRuleError("Produtos inativos não podem ser incluídos.")
        _validate_quantity(product, quantity)
        existing = next(
            (item for item in template.items if item.product_id == product_id), None
        )
        if existing:
            existing.quantity += quantity
            _validate_quantity(product, existing.quantity)
        else:
            template.items.append(
                BasketTemplateItem(product=product, quantity=quantity)
            )
        _touch(template)
        db.flush()
    return template


def update_template_item(
    db: Session, template_id: int, product_id: int, quantity: Decimal
) -> BasketTemplate:
    with db.begin():
        template = _template_or_raise(db, template_id, lock=True)
        item = next(
            (item for item in template.items if item.product_id == product_id), None
        )
        if item is None:
            raise ResourceNotFoundError("Produto não encontrado na composição.")
        product = _product_or_raise(db, item.product_id, lock=True)
        item.product = product
        _validate_quantity(product, quantity)
        item.quantity = quantity
        _touch(template)
        db.flush()
    return template


def remove_template_item(
    db: Session, template_id: int, product_id: int
) -> BasketTemplate:
    with db.begin():
        template = _template_or_raise(db, template_id, lock=True)
        item = next(
            (item for item in template.items if item.product_id == product_id), None
        )
        if item is None:
            raise ResourceNotFoundError("Produto não encontrado na composição.")
        template.items.remove(item)
        _touch(template)
        db.flush()
    return template


def replace_template_item(
    db: Session, template_id: int, source_product_id: int, target_product_id: int
) -> BasketTemplate:
    if source_product_id == target_product_id:
        raise BusinessRuleError("Escolha um produto diferente para a substituição.")
    with db.begin():
        template = _template_or_raise(db, template_id, lock=True)
        source = next(
            (item for item in template.items if item.product_id == source_product_id),
            None,
        )
        if source is None:
            raise ResourceNotFoundError("Produto não encontrado na composição.")
        target_product = _product_or_raise(db, target_product_id, lock=True)
        if not target_product.active:
            raise BusinessRuleError("Produtos inativos não podem ser incluídos.")
        _validate_quantity(target_product, source.quantity)
        target = next(
            (item for item in template.items if item.product_id == target_product_id),
            None,
        )
        if target:
            target.quantity += source.quantity
            _validate_quantity(target_product, target.quantity)
            template.items.remove(source)
        else:
            source.product = target_product
        _touch(template)
        db.flush()
    return template


def _base_unit_reference_price(product: Product) -> Decimal | None:
    """Calculate the reference price per base unit.

    If the product has a commercial_conversion_factor, the reference_price
    is divided by it to get the price per base unit.
    Otherwise, the reference_price is already per base unit.
    """
    if product.reference_price is None:
        return None
    if product.commercial_conversion_factor is not None:
        return (product.reference_price / product.commercial_conversion_factor).quantize(
            Decimal("0.01")
        )
    return product.reference_price


def _calculate_composition_metrics(
    db: Session, items: list[BasketTemplateItem]
) -> tuple[list[ProductCompositionRead], Decimal | None, Decimal | None, bool]:
    if not items:
        return [], None, None, False
    products = [item.product for item in items]
    balances = product_balances(db, products)

    comp_items: list[ProductCompositionRead] = []
    has_reliable_cost = True
    total_reference_cost = Decimal("0.00")

    for item in items:
        product = item.product
        base_price = _base_unit_reference_price(product)
        if base_price is None:
            has_reliable_cost = False
            item_total_cost = None
        else:
            item_total_cost = (item.quantity * base_price).quantize(
                Decimal("0.01")
            )
            total_reference_cost += item.quantity * base_price

        comp_items.append(
            ProductCompositionRead(
                **_composition_item(
                    product=product,
                    quantity=item.quantity,
                    balance=balances[product.id],
                    unit_cost=base_price,
                    total_cost=item_total_cost,
                )
            )
        )

    if has_reliable_cost:
        reference_cost = total_reference_cost.quantize(Decimal("0.01"))
        suggested_price = (reference_cost * Decimal(2)).quantize(Decimal("0.01"))
    else:
        reference_cost = None
        suggested_price = None

    return comp_items, reference_cost, suggested_price, has_reliable_cost


def template_read(db: Session, template: BasketTemplate) -> BasketTemplateRead:
    comp_items, reference_cost, suggested_price, has_reliable_cost = (
        _calculate_composition_metrics(db, template.items)
    )
    return BasketTemplateRead(
        id=template.id,
        name=template.name,
        active=template.active,
        price=template.price,
        estimated_cost=reference_cost,
        suggested_price=suggested_price,
        has_reliable_cost=has_reliable_cost,
        created_at=template.created_at,
        updated_at=template.updated_at,
        items=comp_items,
    )


def _composition_item(
    product: Product,
    quantity: Decimal,
    balance: Decimal,
    unit_cost: Decimal | None = None,
    total_cost: Decimal | None = None,
) -> dict:
    shortage = max(Decimal(0), quantity - balance)
    return {
        "product_id": product.id,
        "product_name": product.name,
        "product_active": product.active,
        "base_unit": product.base_unit,
        "quantity": quantity,
        "inventory_balance": balance,
        "stock_available": shortage == 0,
        "stock_shortage": shortage,
        "unit_cost": unit_cost,
        "total_cost": total_cost,
    }
