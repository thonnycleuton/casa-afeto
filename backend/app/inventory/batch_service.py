from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import case, nulls_last, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.inventory.models import StockBatch
from app.products.models import MovementType


def create_batch(
    db: Session,
    product_id: int,
    quantity: Decimal,
    unit_cost: Decimal | None,
    purchase_id: int | None = None,
    purchase_item_id: int | None = None,
    expiry_date: date | None = None,
) -> StockBatch:
    """Create a new stock batch from an ENTRY movement.
    
    Each ENTRY creates exactly one batch (LOT-001, LOT-002).
    """
    batch = StockBatch(
        product_id=product_id,
        purchase_id=purchase_id,
        purchase_item_id=purchase_item_id,
        quantity_original=quantity,
        quantity_remaining=quantity,
        unit_cost=unit_cost,
        expiry_date=expiry_date,
        status="ACTIVE",
    )
    db.add(batch)
    db.flush()
    db.refresh(batch)
    return batch


def list_batches(
    db: Session,
    product_id: int,
    *,
    include_exhausted: bool = False,
) -> list[StockBatch]:
    """List stock batches for a product, ordered by creation date (FIFO order).
    
    By default returns only ACTIVE batches. Set include_exhausted=True for full history.
    """
    stmt = select(StockBatch).where(StockBatch.product_id == product_id)
    if not include_exhausted:
        stmt = stmt.where(StockBatch.status == "ACTIVE")
    stmt = stmt.order_by(StockBatch.created_at, StockBatch.id)
    return list(db.scalars(stmt).all())


def get_batch(db: Session, batch_id: int) -> StockBatch | None:
    """Get a specific batch by ID."""
    return db.scalar(
        select(StockBatch).where(StockBatch.id == batch_id)
    )


def consume_fifo(
    db: Session,
    product_id: int,
    quantity: Decimal,
) -> list[tuple[StockBatch, Decimal]]:
    """Consume stock batches in FEFO order (First Expired, First Out).
    
    Returns a list of (batch, consumed_quantity) tuples showing how much
    was consumed from each batch.
    
    EXP-005: Batches with expiry_date are consumed first (soonest expiry first).
    Batches without expiry_date fall back to FIFO (created_at ASC).
    If a batch doesn't have enough quantity, consume the rest and continue
    to the next batch.
    
    LOT-010: Uses SELECT FOR UPDATE for concurrency safety.
    """
    if quantity <= 0:
        raise BusinessRuleError("A quantidade de consumo deve ser positiva.")
    
    # FEFO ordering: batches with expiry_date first (soonest expiry),
    # then batches without expiry_date (by created_at ASC)
    stmt = (
        select(StockBatch)
        .where(StockBatch.product_id == product_id, StockBatch.status == "ACTIVE")
        .order_by(
            # Batches with expiry_date come first (NULLs last)
            nulls_last(StockBatch.expiry_date),
            # Within same expiry group, order by expiry_date ASC, then created_at ASC
            StockBatch.expiry_date.asc(),
            StockBatch.created_at.asc(),
            StockBatch.id.asc(),
        )
        .with_for_update()
    )
    batches = list(db.scalars(stmt).all())
    
    if not batches:
        raise BusinessRuleError(
            f"Nenhum lote ativo encontrado para o produto {product_id}."
        )
    
    # Check total available quantity
    total_available = sum(b.quantity_remaining for b in batches)
    if total_available < quantity:
        raise BusinessRuleError(
            f"Estoque insuficiente. Disponível: {total_available}. "
            f"Necessário: {quantity}."
        )
    
    # Consume from oldest batch first
    remaining = quantity
    consumed: list[tuple[StockBatch, Decimal]] = []
    
    for batch in batches:
        if remaining <= 0:
            break
        
        can_consume = min(remaining, batch.quantity_remaining)
        batch.quantity_remaining -= can_consume
        remaining -= can_consume
        consumed.append((batch, can_consume))
        
        if batch.quantity_remaining == 0:
            batch.status = "EXHAUSTED"
    
    return consumed


def get_active_batch_quantity(db: Session, product_id: int) -> Decimal:
    """Get total quantity from all active batches for a product.
    
    This is the physical stock according to LOT-008.
    """
    from sqlalchemy import func
    
    value = db.scalar(
        select(func.coalesce(func.sum(StockBatch.quantity_remaining), 0)).where(
            StockBatch.product_id == product_id,
            StockBatch.status == "ACTIVE",
        )
    )
    return Decimal(value)


def calculate_expiry_status(expiry_date: date | None, threshold_days: int = 7) -> str | None:
    """Calculate the expiry status of a batch.
    
    EXP-006: Returns "EXPIRED" if past expiry date, "WARNING" if within threshold,
    "OK" if plenty of time remaining, or None if no expiry date is set.
    """
    if expiry_date is None:
        return None
    
    today = datetime.now().date()
    days_until = (expiry_date - today).days
    
    if days_until < 0:
        return "EXPIRED"
    elif days_until <= threshold_days:
        return "WARNING"
    else:
        return "OK"


def get_expiry_status_for_batch(batch: StockBatch, threshold_days: int = 7) -> str | None:
    """Get the expiry status for a batch with the calculated field."""
    return calculate_expiry_status(batch.expiry_date, threshold_days)
