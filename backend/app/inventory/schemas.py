from datetime import datetime
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
    created_at: datetime
