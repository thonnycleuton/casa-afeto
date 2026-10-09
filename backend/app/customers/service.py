from __future__ import annotations

import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.customers.models import Customer, CustomerStatus
from app.customers.schemas import CustomerCreate, CustomerUpdate


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", value.lower().strip())
    return "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    ).strip()


def normalize_phone(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def find_duplicate_phone(
    db: Session, phone: str, *, exclude_id: int | None = None
) -> bool:
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return False
    statement = select(Customer.id).where(Customer.phone == normalized_phone)
    if exclude_id is not None:
        statement = statement.where(Customer.id != exclude_id)
    return db.scalar(statement) is not None


def _customer_or_raise(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise ResourceNotFoundError("Cliente não encontrado.")
    return customer


def create_customer(db: Session, payload: CustomerCreate) -> Customer:
    with db.begin():
        customer = Customer(
            name=payload.name,
            phone=normalize_phone(payload.phone),
            email=payload.email.strip() if payload.email else None,
            notes=payload.notes.strip() if payload.notes else None,
            status=CustomerStatus.ACTIVE.value,
        )
        db.add(customer)
        db.flush()
        db.refresh(customer)
    return customer


def get_customer(db: Session, customer_id: int) -> Customer:
    return _customer_or_raise(db, customer_id)


def list_customers(
    db: Session,
    *,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Customer], int]:
    statement = select(Customer).order_by(Customer.name.asc(), Customer.id.asc())
    customers = list(db.scalars(statement).all())
    if status and status.upper() not in {"ACTIVE", "INACTIVE", "ALL"}:
        raise ValueError("Status do cliente é inválido.")
    if status and status.upper() != "ALL":
        customers = [customer for customer in customers if customer.status == status.upper()]
    if search and search.strip():
        search_term = normalize_text(search)
        phone_term = normalize_phone(search)
        customers = [
            customer
            for customer in customers
            if (
                search_term in normalize_text(customer.name)
                or (phone_term and phone_term in normalize_phone(customer.phone))
            )
        ]
    if status is None:
        customers = [customer for customer in customers if customer.status == CustomerStatus.ACTIVE.value]
    total = len(customers)
    start = (page - 1) * page_size
    end = start + page_size
    return customers[start:end], total


def update_customer(
    db: Session, customer_id: int, payload: CustomerUpdate
) -> Customer:
    with db.begin():
        customer = _customer_or_raise(db, customer_id)
        if payload.name is not None:
            customer.name = payload.name
        if payload.phone is not None:
            customer.phone = normalize_phone(payload.phone)
        if "email" in payload.model_fields_set:
            customer.email = (
                payload.email.strip()
                if payload.email and payload.email.strip()
                else None
            )
        if "notes" in payload.model_fields_set:
            customer.notes = (
                payload.notes.strip()
                if payload.notes and payload.notes.strip()
                else None
            )
        db.flush()
        db.refresh(customer)
    return customer


def set_customer_status(db: Session, customer_id: int, status: CustomerStatus) -> Customer:
    with db.begin():
        customer = _customer_or_raise(db, customer_id)
        customer.status = status.value
        db.flush()
        db.refresh(customer)
    return customer
