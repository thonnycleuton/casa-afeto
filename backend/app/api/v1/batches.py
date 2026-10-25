from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.inventory.batch_service import calculate_expiry_status, get_batch, list_batches
from app.inventory.schemas import StockBatchRead

router = APIRouter(prefix="/products/{product_id}/batches", tags=["stock batches"])


@router.get("", response_model=list[StockBatchRead])
def get_product_batches(
    product_id: int,
    include_exhausted: bool = False,
    db: Session = Depends(get_db),
) -> list[StockBatchRead]:
    """List stock batches for a product."""
    batches = list_batches(db, product_id, include_exhausted=include_exhausted)
    return [
        StockBatchRead(
            id=batch.id,
            product_id=batch.product_id,
            purchase_id=batch.purchase_id,
            purchase_item_id=batch.purchase_item_id,
            quantity_original=batch.quantity_original,
            quantity_remaining=batch.quantity_remaining,
            unit_cost=batch.unit_cost,
            status=batch.status,
            expiry_date=batch.expiry_date,
            expiry_status=calculate_expiry_status(batch.expiry_date),
            created_at=batch.created_at,
        )
        for batch in batches
    ]


@router.get("/{batch_id}", response_model=StockBatchRead)
def get_batch_detail(
    product_id: int,
    batch_id: int,
    db: Session = Depends(get_db),
) -> StockBatchRead:
    """Get a specific batch detail."""
    batch = get_batch(db, batch_id)
    if batch is None or batch.product_id != product_id:
        raise ResourceNotFoundError("Lote não encontrado.")
    return StockBatchRead(
        id=batch.id,
        product_id=batch.product_id,
        purchase_id=batch.purchase_id,
        purchase_item_id=batch.purchase_item_id,
        quantity_original=batch.quantity_original,
        quantity_remaining=batch.quantity_remaining,
        unit_cost=batch.unit_cost,
        status=batch.status,
        expiry_date=batch.expiry_date,
        expiry_status=calculate_expiry_status(batch.expiry_date),
        created_at=batch.created_at,
    )
