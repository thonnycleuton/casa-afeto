import os
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.customers.models import Customer
from app.customers.schemas import (
    CustomerCreate,
    CustomerRead,
    CustomerStatusUpdate,
    CustomerUpdate,
)
from app.customers.service import (
    create_customer,
    find_duplicate_phone,
    get_customer,
    list_customers,
    set_customer_status,
    update_customer,
)
from app.important_dates.schemas import (
    ImportantDateCreate,
    ImportantDateRead,
    ImportantDateStatusUpdate,
    ImportantDateUpdate,
)
from app.important_dates.service import (
    create_important_date,
    list_important_dates,
    set_important_date_status,
    update_important_date,
)

router = APIRouter(prefix="/customers", tags=["customers"])


def _customer_response(customer: Customer, *, warning: dict[str, str] | None = None) -> CustomerRead:
    data = CustomerRead.model_validate(customer, from_attributes=True)
    data.warning = warning
    return data


@router.get("", response_model=list[CustomerRead])
def list_customer_records(
    search: str | None = Query(default=None),
    status: Literal["ACTIVE", "INACTIVE", "ALL"] | None = Query(default="ACTIVE"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    db: Session = Depends(get_db),
) -> list[CustomerRead]:
    customers, _ = list_customers(
        db,
        search=search,
        status=status,
        page=page,
        page_size=page_size,
    )
    return [_customer_response(customer) for customer in customers]


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer_record(
    payload: CustomerCreate, db: Session = Depends(get_db)
) -> CustomerRead:
    customer = create_customer(db, payload)
    duplicate = find_duplicate_phone(db, customer.phone, exclude_id=customer.id)
    warning = {"code": "DUPLICATE_PHONE"} if duplicate else None
    return _customer_response(customer, warning=warning)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer_record(
    customer_id: int, db: Session = Depends(get_db)
) -> CustomerRead:
    return _customer_response(get_customer(db, customer_id))


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer_record(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
) -> CustomerRead:
    customer = update_customer(db, customer_id, payload)
    duplicate = find_duplicate_phone(db, customer.phone, exclude_id=customer.id)
    warning = {"code": "DUPLICATE_PHONE"} if duplicate else None
    return _customer_response(customer, warning=warning)


@router.patch("/{customer_id}/status", response_model=CustomerRead)
def set_customer_record_status(
    customer_id: int,
    payload: CustomerStatusUpdate,
    db: Session = Depends(get_db),
) -> CustomerRead:
    customer = set_customer_status(db, customer_id, payload.status)
    return _customer_response(customer)


@router.get("/{customer_id}/important-dates", response_model=list[ImportantDateRead])
def list_customer_dates(
    customer_id: int, db: Session = Depends(get_db)
) -> list[ImportantDateRead]:
    return [
        ImportantDateRead.model_validate(date_record, from_attributes=True)
        for date_record in list_important_dates(db, customer_id)
    ]


@router.post(
    "/{customer_id}/important-dates",
    response_model=ImportantDateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_customer_date(
    customer_id: int,
    payload: ImportantDateCreate,
    db: Session = Depends(get_db),
) -> ImportantDateRead:
    date_record = create_important_date(db, customer_id, payload)
    return ImportantDateRead.model_validate(date_record, from_attributes=True)


@router.put("/{customer_id}/important-dates/{date_id}", response_model=ImportantDateRead)
def update_customer_date(
    customer_id: int,
    date_id: int,
    payload: ImportantDateUpdate,
    db: Session = Depends(get_db),
) -> ImportantDateRead:
    date_record = update_important_date(db, customer_id, date_id, payload)
    return ImportantDateRead.model_validate(date_record, from_attributes=True)


@router.patch(
    "/{customer_id}/important-dates/{date_id}/status",
    response_model=ImportantDateRead,
)
def set_customer_date_status(
    customer_id: int,
    date_id: int,
    payload: ImportantDateStatusUpdate,
    db: Session = Depends(get_db),
) -> ImportantDateRead:
    date_record = set_important_date_status(db, customer_id, date_id, payload.status)
    return ImportantDateRead.model_validate(date_record, from_attributes=True)


@router.post(
    "/{customer_id}/image",
    response_model=CustomerRead,
)
async def upload_customer_image(
    customer_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> CustomerRead:
    """Upload an image for a customer."""
    # Validate file type
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de arquivo não permitido. Use JPEG, PNG, WebP ou GIF.",
        )

    # Read and validate file size
    content = await file.read()
    if len(content) > settings.MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Imagem muito grande. Tamanho máximo: 5 MB.",
        )

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"

    # Ensure upload directory exists
    upload_dir = settings.entity_upload_path("customers")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename

    # Save file
    with open(filepath, "wb") as f:
        f.write(content)

    # Update customer with image URL
    from app.customers.schemas import CustomerUpdate

    customer = update_customer(
        db, customer_id, CustomerUpdate(image_url=f"/api/v1/customers/uploads/{filename}")
    )
    return _customer_response(customer)
