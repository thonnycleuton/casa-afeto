from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.sales.inspection_schemas import (
    InspectionRead,
    InspectionRecordPayload,
    ReintegrationPayload,
)
from app.sales.service import (
    get_inspections_for_sale,
    record_inspection,
    reintegrate_inspection,
)

router = APIRouter(prefix="/sales/{sale_id}/inspections", tags=["inspections"])


@router.get("", response_model=list[InspectionRead])
def list_inspections(
    sale_id: int,
    db: Session = Depends(get_db),
) -> list[InspectionRead]:
    inspections = get_inspections_for_sale(db, sale_id)
    return [InspectionRead.model_validate(i, from_attributes=True) for i in inspections]


@router.post("/{inspection_id}/record", response_model=InspectionRead)
def record_inspection_result(
    sale_id: int,
    inspection_id: int,
    payload: InspectionRecordPayload,
    db: Session = Depends(get_db),
) -> InspectionRead:
    inspection = record_inspection(
        db,
        inspection_id=inspection_id,
        inspected_quantity=payload.inspected_quantity,
        reusable_quantity=payload.reusable_quantity,
        operator_name=payload.operator_name,
    )
    return InspectionRead.model_validate(inspection, from_attributes=True)


@router.post("/{inspection_id}/reintegrate", response_model=InspectionRead)
def reintegrate_inspection_result(
    sale_id: int,
    inspection_id: int,
    payload: ReintegrationPayload,
    db: Session = Depends(get_db),
) -> InspectionRead:
    inspection = reintegrate_inspection(
        db,
        inspection_id=inspection_id,
        quantity=payload.quantity,
    )
    return InspectionRead.model_validate(inspection, from_attributes=True)
