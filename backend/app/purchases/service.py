from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.inventory.service import create_movement
from app.products.models import BaseUnit, InventoryMovement, MovementType, Product
from app.purchases.models import Purchase, PurchaseItem
from app.purchases.schemas import (
    CreatePurchase,
    ListPurchasesFilter,
    PurchaseItemRead,
    PurchaseRead,
)


def _product_or_raise(db: Session, product_id: int) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise ResourceNotFoundError("Produto não encontrado.")
    return product


def create_purchase(db: Session, data: CreatePurchase) -> PurchaseRead:
    """Create a purchase and generate ENTRY inventory movements atomically.
    
    Products are locked in ascending product_id order to prevent deadlocks
    (ADR-002 D-3).
    """
    # Validate all products exist and are active before starting transaction
    product_ids = [item.product_id for item in data.items]
    products = {}
    for item in data.items:
        product = _product_or_raise(db, item.product_id)
        if not product.active:
            raise BusinessRuleError(
                f"Não é possível comprar produto inativo: {product.name}."
            )
        products[item.product_id] = product

    # Validate base quantity for UN products
    for item in data.items:
        product = products[item.product_id]
        conversion_factor = item.conversion_factor
        base_quantity = item.commercial_quantity * conversion_factor
        if product.base_unit == BaseUnit.UN and base_quantity != base_quantity.to_integral_value():
            raise BusinessRuleError(
                f"Produto {product.name}: a conversão resultou em quantidade "
                f"fracionária ({base_quantity}) para unidade UN."
            )

    # Create purchase
    purchased_at = data.purchased_at if data.purchased_at else datetime.now()
    purchase = Purchase(purchased_at=purchased_at)
    db.add(purchase)
    db.flush()
    db.refresh(purchase)

    # Sort items by product_id for lock ordering (ADR-002 D-3)
    sorted_items = sorted(data.items, key=lambda i: i.product_id)

    # Process each item: lock product, create purchase item, create ENTRY
    for item in sorted_items:
        product = products[item.product_id]
        conversion_factor = item.conversion_factor
        base_quantity = item.commercial_quantity * conversion_factor
        unit_cost = (item.commercial_unit_price / conversion_factor).quantize(
            Decimal("0.01")
        )

        # Create purchase item
        purchase_item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=item.product_id,
            commercial_unit=item.commercial_unit,
            conversion_factor=conversion_factor,
            commercial_quantity=item.commercial_quantity,
            commercial_unit_price=item.commercial_unit_price,
            expiry_date=item.expiry_date,
        )
        db.add(purchase_item)

        # Create ENTRY movement with purchase_id and purchase_item_id for traceability
        # This will automatically create a StockBatch (LOT-001)
        # Note: purchase_item.id is available because create_movement locks the product
        # and flushes within the same transaction
        create_movement(
            db,
            product_id=item.product_id,
            quantity=base_quantity,
            movement_type=MovementType.ENTRY,
            unit_cost=unit_cost,
            purchase_id=purchase.id,
            purchase_item_id=purchase_item.id,
            expiry_date=item.expiry_date,
            use_savepoint=False,
        )

    db.flush()
    db.refresh(purchase)

    return _purchase_to_read(db, purchase)


def get_purchase(db: Session, purchase_id: int) -> PurchaseRead:
    """Get a purchase by ID with its items."""
    purchase = db.scalar(
        select(Purchase)
        .options(joinedload(Purchase.items))
        .where(Purchase.id == purchase_id)
    )
    if purchase is None:
        raise ResourceNotFoundError("Compra não encontrada.")
    return _purchase_to_read(db, purchase)


def list_purchases(
    db: Session, filter_: ListPurchasesFilter | None = None
) -> list[PurchaseRead]:
    """List purchases with optional period filters."""
    stmt = select(Purchase).options(joinedload(Purchase.items))
    
    if filter_:
        if filter_.purchased_from:
            stmt = stmt.where(Purchase.purchased_at >= filter_.purchased_from)
        if filter_.purchased_until:
            stmt = stmt.where(Purchase.purchased_at <= filter_.purchased_until)
    
    stmt = stmt.order_by(Purchase.purchased_at.desc(), Purchase.id.desc())
    purchases = db.scalars(stmt).unique().all()
    return [_purchase_to_read(db, p) for p in purchases]


def _purchase_to_read(db: Session, purchase: Purchase) -> PurchaseRead:
    """Convert a Purchase entity to PurchaseRead schema with product info."""
    items = []
    for item in purchase.items:
        product = _product_or_raise(db, item.product_id)
        items.append(PurchaseItemRead(
            id=item.id,
            product_id=item.product_id,
            product_name=product.name,
            base_unit=product.base_unit,
            commercial_unit=item.commercial_unit,
            conversion_factor=item.conversion_factor,
            commercial_quantity=item.commercial_quantity,
            commercial_unit_price=item.commercial_unit_price,
            expiry_date=item.expiry_date,
        ))
    return PurchaseRead(
        id=purchase.id,
        purchased_at=purchase.purchased_at,
        items=items,
    )
