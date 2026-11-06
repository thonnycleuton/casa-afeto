from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BusinessRuleError, ResourceNotFoundError
from app.inventory.service import create_movement
from app.products.models import BaseUnit, InventoryMovement, MovementType, Product
from app.purchases.models import Purchase, PurchaseItem, PurchaseDocumentDiscount
from app.purchases.schemas import (
    CreateDraft,
    CreatePurchase,
    DocumentDiscountRead,
    ListPurchasesFilter,
    PurchaseItemRead,
    PurchaseRead,
    UpdateDraft,
)


def _product_or_raise(db: Session, product_id: int) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise ResourceNotFoundError("Produto não encontrado.")
    return product


def _generate_entries(
    db: Session,
    purchase: Purchase,
    items: list[PurchaseItem],
) -> None:
    """Generate ENTRY inventory movements for each purchase item.
    
    Items are processed in ascending product_id order (ADR-002 D-3).
    Does NOT flush or commit — caller is responsible.
    """
    sorted_items = sorted(items, key=lambda i: i.product_id)
    for item in sorted_items:
        base_quantity = item.commercial_quantity * item.conversion_factor
        unit_cost = (item.commercial_unit_price / item.conversion_factor).quantize(
            Decimal("0.01")
        )
        create_movement(
            db,
            product_id=item.product_id,
            quantity=base_quantity,
            movement_type=MovementType.ENTRY,
            unit_cost=unit_cost,
            purchase_id=purchase.id,
            purchase_item_id=item.id,
            expiry_date=item.expiry_date,
            use_savepoint=False,
        )


def create_purchase(db: Session, data: CreatePurchase) -> PurchaseRead:
    """Create a purchase and generate ENTRY inventory movements atomically.
    
    Products are locked in ascending product_id order to prevent deadlocks
    (ADR-002 D-3).
    """
    # Validate all products exist and are active before starting transaction
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
    purchase = Purchase(
        purchased_at=purchased_at,
        access_key=data.access_key,
        supplier_name=data.supplier_name,
        cnpj=data.cnpj,
        invoice_number=data.invoice_number,
    )
    db.add(purchase)
    db.flush()
    db.refresh(purchase)

    # Create purchase items
    purchase_items = []
    for item in data.items:
        purchase_item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=item.product_id,
            commercial_unit=item.commercial_unit,
            conversion_factor=item.conversion_factor,
            commercial_quantity=item.commercial_quantity,
            commercial_unit_price=item.commercial_unit_price,
            expiry_date=item.expiry_date,
        )
        db.add(purchase_item)
        purchase_items.append(purchase_item)
    db.flush()

    # Generate ENTRY movements
    _generate_entries(db, purchase, purchase_items)

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
    """Convert a Purchase entity to PurchaseRead schema with product info and discounts."""
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
            item_discounts=item.item_discounts,
        ))
    document_discounts = [
        DocumentDiscountRead(
            id=disc.id,
            value=disc.value,
            nature=disc.nature,
            description=disc.description,
        )
        for disc in purchase.document_discounts
    ]
    return PurchaseRead(
        id=purchase.id,
        purchased_at=purchase.purchased_at,
        access_key=purchase.access_key,
        status=purchase.status,
        supplier_name=purchase.supplier_name,
        cnpj=purchase.cnpj,
        invoice_number=purchase.invoice_number,
        document_path=purchase.document_path,
        items=items,
        document_discounts=document_discounts,
    )


def _validate_draft_items(db: Session, items) -> None:
    """Validate products for draft items — active status and UN conversion.
    
    Reuses the same validation logic as create_purchase() without generating
    inventory movements.
    """
    for item in items:
        product = _product_or_raise(db, item.product_id)
        if not product.active:
            raise BusinessRuleError(
                f"Não é possível comprar produto inativo: {product.name}."
            )
        base_quantity = item.commercial_quantity * item.conversion_factor
        if product.base_unit == BaseUnit.UN and base_quantity != base_quantity.to_integral_value():
            raise BusinessRuleError(
                f"Produto {product.name}: a conversão resultou em quantidade "
                f"fracionária ({base_quantity}) para unidade UN."
            )


def create_draft(db: Session, data: CreateDraft) -> PurchaseRead:
    """Create a DRAFT purchase without generating ENTRY movements.
    
    Validates products (active, conversion) like create_purchase(),
    but does NOT call create_movement().
    """
    # Validate products if items provided
    if data.items:
        _validate_draft_items(db, data.items)

    # Create DRAFT purchase
    purchased_at = data.purchased_at if data.purchased_at else datetime.now()
    purchase = Purchase(
        purchased_at=purchased_at,
        status="DRAFT",
        access_key=data.access_key,
        supplier_name=data.supplier_name,
        cnpj=data.cnpj,
        invoice_number=data.invoice_number,
        document_path=data.document_path,
    )
    db.add(purchase)
    db.flush()
    db.refresh(purchase)

    # Create items — no ENTRY movements
    for item in data.items:
        discounts = item.item_discounts
        purchase_item = PurchaseItem(
            purchase_id=purchase.id,
            product_id=item.product_id,
            commercial_unit=item.commercial_unit,
            conversion_factor=item.conversion_factor,
            commercial_quantity=item.commercial_quantity,
            commercial_unit_price=item.commercial_unit_price,
            expiry_date=item.expiry_date,
            item_discounts=(
                [
                    {k: (float(v) if isinstance(v, Decimal) else v)
                     for k, v in d.model_dump(exclude_none=True).items()}
                    for d in discounts
                ]
                if discounts else None
            ),
        )
        db.add(purchase_item)

    # Create document discounts
    if data.document_discounts:
        for disc in data.document_discounts:
            doc_disc = PurchaseDocumentDiscount(
                purchase_id=purchase.id,
                value=disc.value,
                nature=disc.nature,
                description=disc.description,
            )
            db.add(doc_disc)

    db.flush()
    db.refresh(purchase)
    return _purchase_to_read(db, purchase)


def update_draft(db: Session, purchase_id: int, data: UpdateDraft) -> PurchaseRead:
    """Update a purchase based on its status.
    
    DRAFT: allow full edit of data and items.
    CONFIRMED: allow only fiscal/descriptive data; reject items with 409.
    
    Uses model_fields_set to distinguish omitted fields from explicitly sent ones.
    Always preserves document_path unless explicitly provided.
    """
    purchase = db.scalar(
        select(Purchase)
        .options(joinedload(Purchase.items))
        .where(Purchase.id == purchase_id)
    )
    if purchase is None:
        raise ResourceNotFoundError("Compra não encontrada.")

    # CONFIRMED: reject any items modification (including empty list)
    if purchase.status == "CONFIRMED" and "items" in data.model_fields_set:
        raise BusinessRuleError(
            "Não é possível alterar itens de uma compra confirmada."
        )

    # CONFIRMED: reject any document_discounts modification (including empty list)
    if purchase.status == "CONFIRMED" and "document_discounts" in data.model_fields_set:
        raise BusinessRuleError(
            "Não é possível alterar descontos de uma compra confirmada."
        )

    # Update only the fields that were explicitly sent
    fields_set = data.model_fields_set

    # Note: document_path is NOT editable via PATCH — set only by backend (OCR).
    if "purchased_at" in fields_set and data.purchased_at is not None:
        purchase.purchased_at = data.purchased_at
    if "supplier_name" in fields_set:
        purchase.supplier_name = data.supplier_name
    if "cnpj" in fields_set:
        purchase.cnpj = data.cnpj
    if "invoice_number" in fields_set:
        purchase.invoice_number = data.invoice_number

    # DRAFT: update items if explicitly provided
    if purchase.status == "DRAFT" and "items" in data.model_fields_set:
        # Validate ALL new items before replacing existing ones
        if data.items:
            _validate_draft_items(db, data.items)

        # Delete existing items
        db.query(PurchaseItem).where(
            PurchaseItem.purchase_id == purchase_id
        ).delete(synchronize_session=False)

        # Create new items
        if data.items:
            for item in data.items:
                discounts = item.item_discounts
                purchase_item = PurchaseItem(
                    purchase_id=purchase_id,
                    product_id=item.product_id,
                    commercial_unit=item.commercial_unit,
                    conversion_factor=item.conversion_factor,
                    commercial_quantity=item.commercial_quantity,
                    commercial_unit_price=item.commercial_unit_price,
                    expiry_date=item.expiry_date,
                    item_discounts=(
                        [
                            {k: (float(v) if isinstance(v, Decimal) else v)
                             for k, v in d.model_dump(exclude_none=True).items()}
                            for d in discounts
                        ]
                        if discounts else None
                    ),
                )
                db.add(purchase_item)

    # Update document discounts if explicitly provided
    if "document_discounts" in data.model_fields_set:
        # Replace all document discounts
        db.query(PurchaseDocumentDiscount).where(
            PurchaseDocumentDiscount.purchase_id == purchase_id
        ).delete(synchronize_session=False)
        if data.document_discounts:
            for disc in data.document_discounts:
                doc_disc = PurchaseDocumentDiscount(
                    purchase_id=purchase_id,
                    value=disc.value,
                    nature=disc.nature,
                    description=disc.description,
                )
                db.add(doc_disc)

    db.flush()
    db.refresh(purchase)
    return _purchase_to_read(db, purchase)


def confirm_purchase(db: Session, purchase_id: int) -> PurchaseRead:
    """Confirm a DRAFT purchase: generate ENTRY movements and set status to CONFIRMED.
    
    Uses SELECT FOR UPDATE to prevent concurrent confirmation.
    Only DRAFT purchases can be confirmed. CONFIRMED purchases are rejected (409).
    Re-validates products (active, UN conversion) at confirmation time.
    If any validation fails, no ENTRY is generated and the purchase remains DRAFT.
    """
    # Lock the purchase row to prevent concurrent confirmation.
    # Use a separate query for items to avoid FOR UPDATE on a LEFT OUTER JOIN
    # (joinedload generates LEFT OUTER JOIN which is not compatible with FOR UPDATE).
    purchase = db.scalar(
        select(Purchase)
        .where(Purchase.id == purchase_id)
        .with_for_update()
    )
    if purchase is None:
        raise ResourceNotFoundError("Compra não encontrada.")

    # Load items in a separate query
    items = db.scalars(
        select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id)
    ).all()

    if purchase.status != "DRAFT":
        raise BusinessRuleError(
            "Somente compras em rascunho podem ser confirmadas."
        )

    if not items:
        raise BusinessRuleError(
            "Não é possível confirmar uma compra sem itens."
        )

    # Re-validate products at confirmation time
    for item in items:
        product = _product_or_raise(db, item.product_id)
        if not product.active:
            raise BusinessRuleError(
                f"Não é possível comprar produto inativo: {product.name}."
            )
        base_quantity = item.commercial_quantity * item.conversion_factor
        if product.base_unit == BaseUnit.UN and base_quantity != base_quantity.to_integral_value():
            raise BusinessRuleError(
                f"Produto {product.name}: a conversão resultou em quantidade "
                f"fracionária ({base_quantity}) para unidade UN."
            )

    # Generate ENTRY movements for all items
    _generate_entries(db, purchase, items)

    # Mark as confirmed
    purchase.status = "CONFIRMED"

    db.flush()
    db.refresh(purchase)
    return _purchase_to_read(db, purchase)
