from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class ReplenishmentItemRead(BaseModel):
    """Um item na lista de reposição — cálculo derivado, não persistido."""

    product_id: int
    product_name: str
    stock_quantity: Decimal
    estimated_need: Decimal
    urgent_need: Decimal
    total_need: Decimal
    shortage: Decimal
    status: str  # "OK", "BAIXO", "CRÍTICO"


class ReplenishmentListRead(BaseModel):
    """Resposta do endpoint de reposição."""

    items: list[ReplenishmentItemRead]
    total: int
