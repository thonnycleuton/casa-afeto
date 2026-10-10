from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.products.models import (
    BaseUnit,
    InventoryMovement,
    MovementType,
    Product,
)
from app.products.schemas import AvailabilityRead, BalanceRead


def _product_or_raise(
    db: Session, product_id: int, *, lock: bool = False
) -> Product:
    statement = select(Product).where(Product.id == product_id)
    if lock:
        statement = statement.with_for_update()
    product = db.scalar(statement)
    if product is None:
        raise ResourceNotFoundError("Produto não encontrado.")
    return product


def _balance(db: Session, product_id: int) -> Decimal:
    value = db.scalar(
        select(func.coalesce(func.sum(InventoryMovement.quantity), 0)).where(
            InventoryMovement.product_id == product_id
        )
    )
    return Decimal(value)


def _validate_quantity(unit: str, quantity: Decimal) -> None:
    if unit == BaseUnit.UN and quantity != quantity.to_integral_value():
        raise BusinessRuleError("As quantidades para UN devem ser números inteiros.")


def product_balance(db: Session, product_id: int) -> BalanceRead:
    product = _product_or_raise(db, product_id)
    return BalanceRead(
        product_id=product.id,
        quantity=_balance(db, product_id),
        base_unit=BaseUnit(product.base_unit),
    )


def product_balances(db: Session, products: list[Product]) -> dict[int, Decimal]:
    if not products:
        return {}
    rows = db.execute(
        select(
            InventoryMovement.product_id,
            func.sum(InventoryMovement.quantity),
        )
        .where(InventoryMovement.product_id.in_([product.id for product in products]))
        .group_by(InventoryMovement.product_id)
    )
    balances = {product_id: Decimal(quantity) for product_id, quantity in rows}
    return {product.id: balances.get(product.id, Decimal(0)) for product in products}


def product_average_costs(
    db: Session, products: list[Product]
) -> dict[int, Decimal | None]:
    if not products:
        return {}
    product_ids = [p.id for p in products]
    rows = db.execute(
        select(
            InventoryMovement.product_id,
            func.sum(InventoryMovement.quantity * InventoryMovement.unit_cost),
            func.sum(InventoryMovement.quantity),
        )
        .where(
            InventoryMovement.product_id.in_(product_ids),
            InventoryMovement.type == MovementType.ENTRY.value,
            InventoryMovement.unit_cost.is_not(None),
        )
        .group_by(InventoryMovement.product_id)
    )
    avg_costs: dict[int, Decimal] = {}
    for product_id, total_cost, total_qty in rows:
        if total_qty is not None and Decimal(total_qty) > 0 and total_cost is not None:
            avg_costs[product_id] = (Decimal(total_cost) / Decimal(total_qty)).quantize(
                Decimal("0.01")
            )
    return {p.id: avg_costs.get(p.id) for p in products}


def product_average_cost(db: Session, product_id: int) -> Decimal | None:
    product = _product_or_raise(db, product_id)
    return product_average_costs(db, [product])[product.id]


def create_movement(
    db: Session,
    product_id: int,
    quantity: Decimal,
    movement_type: MovementType,
    unit_cost: Decimal | None = None,
) -> InventoryMovement:
    if movement_type is MovementType.ENTRY and quantity <= 0:
        raise BusinessRuleError("A quantidade da entrada deve ser maior que zero.")
    if movement_type is MovementType.ADJUSTMENT and quantity == 0:
        raise BusinessRuleError("A quantidade do ajuste não pode ser zero.")
    if movement_type is MovementType.ENTRY and unit_cost is not None:
        if not unit_cost.is_finite() or unit_cost < 0:
            raise BusinessRuleError("O custo unitário não pode ser negativo.")
        unit_cost = unit_cost.quantize(Decimal("0.01"))
    elif movement_type is MovementType.ADJUSTMENT:
        unit_cost = None

    with db.begin():
        product = _product_or_raise(db, product_id, lock=True)
        if not product.active:
            raise BusinessRuleError(
                "Produtos inativos devem ser reativados antes de alterar o estoque."
            )
        _validate_quantity(product.base_unit, quantity)
        current_balance = _balance(db, product_id)
        resulting_balance = current_balance + quantity
        if resulting_balance < 0:
            raise BusinessRuleError(
                f"Estoque insuficiente. Disponível: {current_balance} "
                f"{product.base_unit}. Necessário: {abs(quantity)} {product.base_unit}."
            )
        movement = InventoryMovement(
            product_id=product_id,
            quantity=quantity,
            unit_cost=unit_cost,
            type=movement_type.value,
        )
        db.add(movement)
        db.flush()
        db.refresh(movement)
    return movement



def inventory_history(db: Session, product_id: int) -> list[InventoryMovement]:
    _product_or_raise(db, product_id)
    return list(
        db.scalars(
            select(InventoryMovement)
            .where(InventoryMovement.product_id == product_id)
            .order_by(InventoryMovement.created_at, InventoryMovement.id)
        ).all()
    )


def check_availability(
    db: Session, product_id: int, required_quantity: Decimal
) -> AvailabilityRead:
    product = _product_or_raise(db, product_id)
    _validate_quantity(product.base_unit, required_quantity)
    available_quantity = _balance(db, product_id)
    shortage = max(Decimal(0), required_quantity - available_quantity)
    return AvailabilityRead(
        product_id=product_id,
        available=shortage == 0,
        available_quantity=available_quantity,
        required_quantity=required_quantity,
        shortage=shortage,
        base_unit=BaseUnit(product.base_unit),
    )
