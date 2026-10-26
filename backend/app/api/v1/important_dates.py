"""Endpoint de datas afetivas próximas (M10)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.important_dates.schemas import UpcomingDatesListRead
from app.important_dates.service import get_upcoming_dates

router = APIRouter(tags=["Datas Afetivas"])


@router.get(
    "/important-dates/upcoming",
    response_model=UpcomingDatesListRead,
    summary="Datas afetivas próximas",
)
def upcoming_dates(
    days: int = Query(default=7, ge=1, le=1095, description="Janela de dias à frente (1–1095)"),
    db: Session = Depends(get_db),
) -> UpcomingDatesListRead:
    """Retornar datas afetivas ativas dos próximos N dias.

    IDA-001: Apenas datas ativas são listadas.
    IDA-004: Janela de tempo configurável.
    """
    return get_upcoming_dates(db, days=days)
