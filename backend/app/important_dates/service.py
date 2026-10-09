from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.customers.models import Customer
from app.important_dates.models import ImportantDate, ImportantDateStatus
from app.important_dates.schemas import ImportantDateCreate, ImportantDateUpdate


def _customer_or_raise(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ResourceNotFoundError("Cliente não encontrado.")
    return customer


def _important_date_or_raise(db: Session, customer_id: int, date_id: int) -> ImportantDate:
    important_date = db.scalar(
        select(ImportantDate).where(
            ImportantDate.id == date_id,
            ImportantDate.customer_id == customer_id,
        )
    )
    if important_date is None:
        raise ResourceNotFoundError("Data importante não encontrada para este cliente.")
    return important_date


def create_important_date(
    db: Session, customer_id: int, payload: ImportantDateCreate
) -> ImportantDate:
    with db.begin():
        _customer_or_raise(db, customer_id)
        important_date = ImportantDate(
            customer_id=customer_id,
            description=payload.description,
            recurring=payload.recurring,
            day=payload.day,
            month=payload.month,
            date=payload.date,
            status=ImportantDateStatus.ACTIVE.value,
        )
        db.add(important_date)
        db.flush()
        db.refresh(important_date)
    return important_date


def list_important_dates(db: Session, customer_id: int) -> list[ImportantDate]:
    _customer_or_raise(db, customer_id)
    return list(
        db.scalars(
            select(ImportantDate)
            .where(ImportantDate.customer_id == customer_id)
            .order_by(ImportantDate.description.asc(), ImportantDate.id.asc())
        ).all()
    )


def get_important_date(db: Session, customer_id: int, date_id: int) -> ImportantDate:
    return _important_date_or_raise(db, customer_id, date_id)


def update_important_date(
    db: Session,
    customer_id: int,
    date_id: int,
    payload: ImportantDateUpdate,
) -> ImportantDate:
    with db.begin():
        important_date = _important_date_or_raise(db, customer_id, date_id)
        if payload.description is not None:
            important_date.description = payload.description
        important_date.recurring = payload.recurring
        if payload.day is not None:
            important_date.day = payload.day
        if payload.month is not None:
            important_date.month = payload.month
        if payload.date is not None:
            important_date.date = payload.date
        if payload.recurring is True:
            important_date.date = None
        elif payload.recurring is False:
            important_date.day = None
            important_date.month = None
        db.flush()
        db.refresh(important_date)
    return important_date


def set_important_date_status(
    db: Session, customer_id: int, date_id: int, status: ImportantDateStatus
) -> ImportantDate:
    with db.begin():
        important_date = _important_date_or_raise(db, customer_id, date_id)
        important_date.status = status.value
        db.flush()
        db.refresh(important_date)
    return important_date
