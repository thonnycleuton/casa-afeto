from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.inventory.batch_service import calculate_expiry_status
from app.inventory.models import StockBatch
from app.inventory.schemas import ExpiryAlertRead
from app.products.models import Product

router = APIRouter(prefix="/inventory", tags=["expiry alerts"])


@router.get("/expiry-alerts", response_model=list[ExpiryAlertRead])
def get_expiry_alerts(
    threshold_days: int = Query(7, ge=1, le=365),
    include_expired: bool = Query(True),
    db: Session = Depends(get_db),
) -> list[ExpiryAlertRead]:
    """List all batches with expiry warnings or expired status.
    
    EXP-008: Global list of expiry alerts across all products.
    Ordered by urgency: expired first, then soonest expiry first.
    """
    today = datetime.now().date()
    
    # Build query: only batches with expiry_date
    stmt = select(StockBatch).where(
        StockBatch.expiry_date.isnot(None),
        StockBatch.status == "ACTIVE",
    )
    
    # Filter by status
    if not include_expired:
        # Only WARNING status (not expired)
        stmt = stmt.where(StockBatch.expiry_date >= today)
    
    # Order by expiry_date ASC (most urgent first)
    stmt = stmt.order_by(StockBatch.expiry_date.asc(), StockBatch.created_at.asc())
    
    batches = db.scalars(stmt).all()
    
    results = []
    for batch in batches:
        status = calculate_expiry_status(batch.expiry_date, threshold_days)
        
        # Skip batches that are OK (not within threshold and not expired)
        if status == "OK":
            continue
        
        # Calculate days until expiry
        days_until = (batch.expiry_date - today).days if batch.expiry_date else 0
        
        # Get product name
        product = db.scalar(
            select(Product).where(Product.id == batch.product_id)
        )
        product_name = product.name if product else "Unknown"
        
        results.append(ExpiryAlertRead(
            batch_id=batch.id,
            product_id=batch.product_id,
            product_name=product_name,
            quantity_remaining=batch.quantity_remaining,
            unit_cost=batch.unit_cost,
            expiry_date=batch.expiry_date,
            expiry_status=status,
            days_until_expiry=days_until,
            purchase_id=batch.purchase_id,
        ))
    
    return results
