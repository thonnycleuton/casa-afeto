from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.payments.schemas import PaymentCreate, PaymentRead, PaymentTotalRead
from app.payments.service import get_payments_for_sale, get_total_paid, record_payment

router = APIRouter(prefix="/sales/{sale_id}/payments", tags=["payments"])


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(
    sale_id: int,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
) -> PaymentRead:
    payment = record_payment(
        db,
        sale_id=sale_id,
        amount=payload.amount,
        method=payload.method,
        idempotency_key=payload.idempotency_key,
    )
    db.commit()
    return PaymentRead.model_validate(payment, from_attributes=True)


@router.get("", response_model=list[PaymentRead])
def list_payments(
    sale_id: int,
    db: Session = Depends(get_db),
) -> list[PaymentRead]:
    payments = get_payments_for_sale(db, sale_id)
    return [PaymentRead.model_validate(p, from_attributes=True) for p in payments]


@router.get("/total", response_model=PaymentTotalRead)
def get_payment_total(
    sale_id: int,
    db: Session = Depends(get_db),
) -> PaymentTotalRead:
    from app.sales.service import get_sale

    sale = get_sale(db, sale_id)
    total_paid = get_total_paid(db, sale_id)
    sale_total = sale.total
    if sale_total > 0:
        percentage = (total_paid / sale_total * 100).quantize(Decimal("0.01"))
    else:
        percentage = Decimal("0.00")
    return PaymentTotalRead(
        sale_id=sale_id,
        total_paid=total_paid,
        sale_total=sale_total,
        payment_percentage=percentage,
    )
