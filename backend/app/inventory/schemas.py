from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StockBatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    purchase_id: Optional[int] = None
    purchase_item_id: Optional[int] = None
    quantity_original: Decimal
    quantity_remaining: Decimal
    unit_cost: Optional[Decimal] = None
    status: str
    expiry_date: Optional[date] = None
    expiry_status: Optional[str] = None
    created_at: datetime


class ExpiryAlertRead(BaseModel):
    """Expiry alert for a stock batch."""

    batch_id: int
    product_id: int
    product_name: str
    quantity_remaining: Decimal
    unit_cost: Optional[Decimal] = None
    expiry_date: date
    expiry_status: str
    days_until_expiry: int
    purchase_id: Optional[int] = None
