from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.purchases.schemas import CreateDraft, CreatePurchase, PurchaseRead, UpdateDraft
from app.purchases.service import (
    confirm_purchase,
    create_draft,
    create_purchase,
    get_purchase,
    list_purchases,
    update_draft,
)

router = APIRouter(prefix="/purchases", tags=["purchases"])
bearer = HTTPBearer()


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


@router.post("/draft", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
def create_draft_endpoint(
    payload: CreateDraft,
    db: Session = Depends(get_db),
) -> PurchaseRead:
    """Create a DRAFT purchase without generating ENTRY movements."""
    purchase = create_draft(db, payload)
    db.commit()
    return purchase


@router.patch("/{purchase_id}", response_model=PurchaseRead)
def update_purchase_endpoint(
    purchase_id: int,
    payload: UpdateDraft,
    db: Session = Depends(get_db),
) -> PurchaseRead:
    """Update a purchase — DRAFT allows full edit, CONFIRMED allows fiscal data only."""
    purchase = update_draft(db, purchase_id, payload)
    db.commit()
    return purchase


@router.post("/{purchase_id}/confirm", response_model=PurchaseRead)
def confirm_purchase_endpoint(
    purchase_id: int,
    db: Session = Depends(get_db),
) -> PurchaseRead:
    """Confirm a DRAFT purchase: generate ENTRY movements and set status to CONFIRMED."""
    purchase = confirm_purchase(db, purchase_id)
    db.commit()
    return purchase


@router.get("/{purchase_id}/document")
def get_purchase_document_endpoint(
    purchase_id: int,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Session = Depends(get_db),
) -> FileResponse:
    """Get the original document for a purchase.

    Requires JWT authentication (same as OCR endpoints).
    Returns the file via FileResponse if the purchase has a document_path.
    Returns 404 if the purchase has no document or the file is not available.
    Validates the resolved path to prevent directory traversal attacks.
    """
    # Validate JWT token — same pattern as OCR endpoints
    from app.auth.utils import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    purchase = get_purchase(db, purchase_id)

    if not purchase.document_path:
        raise ResourceNotFoundError("Esta compra não possui documento associado.")

    # Resolve the absolute path from the relative document_path
    # document_path is stored as "purchases/filename.jpg"
    uploads_base = settings.uploads_base_path
    file_path = uploads_base / purchase.document_path

    # Validate path is within uploads directory (prevent directory traversal)
    try:
        file_path.resolve().relative_to(uploads_base.resolve())
    except ValueError:
        raise ResourceNotFoundError("Caminho do documento inválido.")

    if not file_path.exists() or not file_path.is_file():
        raise ResourceNotFoundError("Arquivo do documento não encontrado.")

    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=file_path.name,
    )
