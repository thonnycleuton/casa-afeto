"""Endpoint de reposição de estoque."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.inventory.replenishment_schemas import ReplenishmentListRead
from app.inventory.replenishment_service import get_replenishment_list

router = APIRouter(tags=["Reposição"])


@router.get(
    "/inventory/replenishment",
    response_model=ReplenishmentListRead,
    summary="Lista de reposição",
)
def replenishment_list(
    status: Optional[str] = Query(None, description="Filtrar por status: OK, BAIXO, CRÍTICO"),
    product_id: Optional[int] = Query(None, description="Filtrar por produto"),
    db: Session = Depends(get_db),
) -> ReplenishmentListRead:
    """Retornar a lista de reposição calculada em tempo real.

    REP-008: Lista de reposição é cálculo em tempo real.
    """
    return get_replenishment_list(
        db,
        status_filter=status,
        product_id_filter=product_id,
    )
