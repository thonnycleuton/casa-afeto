from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ResourceNotFoundError
from app.customers.models import Customer
from app.important_dates.models import ImportantDate, ImportantDateStatus
from app.important_dates.schemas import (
    ImportantDateCreate,
    ImportantDateUpdate,
    UpcomingDateRead,
    UpcomingDatesListRead,
)


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


def _is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def _next_occurrence_recurring(day: int, month: int, today: date) -> date:
    """Calcular a próxima ocorrência de uma data recorrente (IDA-002)."""
    year = today.year
    # IDA-002: 29/02 em ano não bissexto — encontra o próximo ano válido
    while day == 29 and month == 2 and not _is_leap_year(year):
        year += 1
    candidate = date(year, month, day)
    if candidate < today:
        year += 1
        while day == 29 and month == 2 and not _is_leap_year(year):
            year += 1
        candidate = date(year, month, day)
    return candidate


def get_upcoming_dates(
    db: Session, days: int = 7, today: date | None = None
) -> UpcomingDatesListRead:
    """Retornar datas afetivas ativas dos próximos N dias (M10).

    IDA-001: Apenas datas ativas são listadas.
    IDA-002: Próxima ocorrência de data recorrente.
    IDA-003: Próxima ocorrência de data não recorrente.
    IDA-004: Janela de tempo configurável.
    IDA-005: Ordenação por próxima ocorrência.
    IDA-006: Cliente inativo não impede listagem.
    """
    if today is None:
        today = date.today()
    end_date = today + timedelta(days=days)

    # Busca todas as datas ativas com o cliente carregado
    dates = (
        db.scalars(
            select(ImportantDate)
            .options(joinedload(ImportantDate.customer))
            .where(ImportantDate.status == ImportantDateStatus.ACTIVE.value)
        )
        .all()
    )

    items: list[UpcomingDateRead] = []
    for imp_date in dates:
        next_occ: date | None = None

        if imp_date.recurring:
            # IDA-002: Data recorrente
            if imp_date.day is not None and imp_date.month is not None:
                next_occ = _next_occurrence_recurring(imp_date.day, imp_date.month, today)
        else:
            # IDA-003: Data não recorrente
            if imp_date.date is not None and imp_date.date >= today:
                next_occ = imp_date.date

        # IDA-004: Filtra pela janela
        if next_occ is not None and today <= next_occ <= end_date:
            items.append(
                UpcomingDateRead(
                    id=imp_date.id,
                    customer_id=imp_date.customer_id,
                    customer_name=imp_date.customer.name,
                    description=imp_date.description,
                    recurring=imp_date.recurring,
                    next_occurrence=next_occ,
                    status=ImportantDateStatus(imp_date.status),
                )
            )

    # IDA-005: Ordena por próxima ocorrência, depois por nome do cliente
    items.sort(key=lambda x: (x.next_occurrence, x.customer_name))

    return UpcomingDatesListRead(items=items, total=len(items))
