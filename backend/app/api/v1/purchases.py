from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.purchases.schemas import CreatePurchase, PurchaseRead
from app.purchases.service import create_purchase, get_purchase, list_purchases

router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
def create_purchase_endpoint(
    payload: CreatePurchase,
    db: Session = Depends(get_db),
) -> PurchaseRead:
    purchase = create_purchase(db, payload)
    db.commit()
    return purchase


@router.get("", response_model=list[PurchaseRead])
def list_purchases_endpoint(
    purchased_from: datetime | None = Query(None),
    purchased_until: datetime | None = Query(None),
    db: Session = Depends(get_db),
) -> list[PurchaseRead]:
    from app.purchases.schemas import ListPurchasesFilter

    filter_ = None
    if purchased_from or purchased_until:
        filter_ = ListPurchasesFilter(
            purchased_from=purchased_from,
            purchased_until=purchased_until,
        )
    return list_purchases(db, filter_)


@router.get("/{purchase_id}", response_model=PurchaseRead)
def get_purchase_endpoint(
    purchase_id: int,
    db: Session = Depends(get_db),
) -> PurchaseRead:
    return get_purchase(db, purchase_id)
