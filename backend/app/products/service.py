from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.products.models import InventoryMovement, Product
from app.products.schemas import ProductCreate, ProductUpdate


def _product_or_raise(db: Session, product_id: int, *, lock: bool = False) -> Product:
    statement = select(Product).where(Product.id == product_id)
    if lock:
        statement = statement.with_for_update()
    product = db.scalar(statement)
    if product is None:
        raise ResourceNotFoundError("Produto não encontrado.")
    return product


def create_product(db: Session, payload: ProductCreate) -> Product:
    with db.begin():
        product = Product(
            name=payload.name,
            base_unit=payload.base_unit.value,
            reference_price=payload.reference_price,
            active=True,
        )
        db.add(product)
        db.flush()
        db.refresh(product)
    return product


def update_product(
    db: Session, product_id: int, payload: ProductUpdate
) -> Product:
    with db.begin():
        product = _product_or_raise(db, product_id, lock=True)
        if payload.name is not None:
            product.name = payload.name
        if payload.base_unit is not None and payload.base_unit.value != product.base_unit:
            movement_exists = db.scalar(
                select(InventoryMovement.id)
                .where(InventoryMovement.product_id == product_id)
                .limit(1)
            )
            if movement_exists is not None:
                raise BusinessRuleError(
                    "A unidade base não pode ser alterada após o registro de movimentações de estoque."
                )
            product.base_unit = payload.base_unit.value
        if "reference_price" in payload.model_fields_set:
            product.reference_price = payload.reference_price
        db.flush()
        db.refresh(product)
    return product


def set_product_active(db: Session, product_id: int, active: bool) -> Product:
    with db.begin():
        product = _product_or_raise(db, product_id, lock=True)
        product.active = active
        db.flush()
        db.refresh(product)
    return product


def list_products(db: Session, search: Optional[str] = None) -> list[Product]:
    statement = select(Product).order_by(Product.name, Product.id)
    if search and search.strip():
        escaped = (
            search.strip()
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        statement = statement.where(Product.name.ilike(f"%{escaped}%", escape="\\"))
    return list(db.scalars(statement).all())
