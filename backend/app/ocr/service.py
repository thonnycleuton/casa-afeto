"""OCR service for M13 — Upload, background processing, session management, and confirmation.

Handles document upload, async Gemini processing via background tasks,
in-memory session management, file cleanup (D-1, D-12, D-13), and
confirmation of imported purchases via create_purchase() (Etapa 3).
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessRuleError
from app.ocr.gemini_client import call_gemini_ocr
from app.ocr.schemas import (
    ConfirmImportRequest,
    ConfirmImportResponse,
    ConfirmImportTotals,
    ConfirmedItemRead,
    ExcludedItemRead,
    OCRDiscount,
    OCRItem,
    OCRSession,
    OCRStatus,
)
from app.ocr.state import store
from app.purchases.schemas import (
    CreateDraft,
    CreateDraftItem,
    DocumentDiscountCreate,
    ItemDiscount,
)
from app.purchases.service import create_draft as _create_draft

logger = logging.getLogger(__name__)

# Accepted content types for OCR upload (D-14)
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Max file size for OCR uploads (10 MB)
MAX_OCR_FILE_SIZE = 10 * 1024 * 1024


def _get_ocr_upload_dir() -> Path:
    """Return the temporary OCR upload directory."""
    return settings.entity_upload_path("ocr")


def _save_upload(file: UploadFile, filename: str) -> Path:
    """Save uploaded file to temporary OCR directory."""
    upload_dir = _get_ocr_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename
    content = file.file.read()
    file_path.write_bytes(content)
    return file_path


def _delete_file_silent(file_path: str | None) -> None:
    """Delete a file silently if it exists."""
    if not file_path:
        return
    try:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.info("Deleted OCR temp file: %s", file_path)
    except OSError as exc:
        logger.warning("Failed to delete OCR temp file %s: %s", file_path, exc)


async def _process_document(session_id: str) -> None:
    """Background task: process document with Gemini and update session.

    Called via asyncio.create_task() from upload_document().
    Updates session status to 'completed' or 'failed'.
    Deletes the temporary file after processing (D-13).
    """
    session = store.get(session_id)
    if session is None:
        logger.error("Session %s not found for processing", session_id)
        return

    # Mark as processing
    session.status = "processing"
    store.update(session)

    model = settings.GEMINI_MODEL
    session.model_used = model
    store.update(session)

    file_path = session.file_path
    try:
        result = call_gemini_ocr(Path(session.file_path), session.file_mime_type)

        # Update session with extracted data
        session.status = "completed"
        session.document_total = result.document_total
        session.purchased_at = result.purchased_at
        session.access_key = result.access_key
        session.items = result.items
        session.document_discounts = result.document_discounts
        session.error = None
        store.update(session)
        logger.info("OCR completed for session %s with %d items", session_id, len(result.items))

        # Do NOT delete temp file on success — preserve until confirm_import copies it
        # to permanent storage (Step 5 requirement).
        # The temp file is deleted after successful draft creation in confirm_import().

    except Exception as exc:
        logger.error("OCR failed for session %s: %s", session_id, exc)
        session.status = "failed"
        session.error = str(exc)
        # Preserve file_path on failure so it remains available for retry
        store.update(session)


def upload_document(file: UploadFile) -> OCRSession:
    """Upload a document for OCR processing.

    Validates file type and size, saves temporarily, creates session,
    and starts background processing.

    Args:
        file: Uploaded image file.

    Returns:
        OCRSession with session_id and initial status.

    Raises:
        ValueError: If file type or size is invalid.
    """
    # Validate content type (D-14)
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        # Try to infer from filename
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        type_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
        inferred = type_map.get(ext)
        if inferred and inferred in ALLOWED_CONTENT_TYPES:
            content_type = inferred
        else:
            raise ValueError(
                f"Tipo de arquivo não suportado: {content_type}. "
                f"Formatos aceitos: JPEG, PNG, WebP."
            )

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    if file_size > MAX_OCR_FILE_SIZE:
        raise ValueError(
            f"Arquivo muito grande: {file_size} bytes. "
            f"Tamanho máximo: {MAX_OCR_FILE_SIZE} bytes."
        )
    if file_size == 0:
        raise ValueError("Arquivo vazio.")

    # Generate session ID and filename
    session_id = uuid.uuid4().hex
    filename = f"{session_id}.jpg"

    # Save file
    file_path = _save_upload(file, filename)

    # Create session
    session = OCRSession(
        session_id=session_id,
        status="pending",
        file_path=str(file_path),
        file_mime_type=content_type,
        items=[],
    )
    store.add(session)

    # Start background processing — protect against task creation failure
    coroutine = _process_document(session_id)
    try:
        asyncio.create_task(coroutine)
    except Exception:
        # Task creation failed: close coroutine and clean up session and temp file
        coroutine.close()
        store.remove(session_id)
        _delete_file_silent(str(file_path))
        raise

    return session


def get_session(session_id: str) -> OCRSession | None:
    """Get an OCR session by ID.

    Returns None if session not found.
    """
    return store.get(session_id)


def reprocess_document(session_id: str) -> None:
    """Reprocess a failed OCR session.

    Atomically claims the session from 'failed' to 'pending', verifies the
    temp file is still available, and schedules background processing.

    Args:
        session_id: The session to reprocess.

    Raises:
        ValueError: If session doesn't exist, isn't failed, file is missing,
                    or another request already claimed the session.
    """
    # 1. Check session exists
    session = store.get(session_id)
    if session is None:
        raise ValueError(f"Sessão {session_id} não encontrada.")

    # 2. Check session is in failed status
    if session.status != "failed":
        raise ValueError(
            f"Sessão {session_id} está em estado '{session.status}', "
            f"não 'failed'. Retentativa só é possível após falha."
        )

    # 3. Check file_path is set and file exists on disk
    if not session.file_path or not Path(session.file_path).exists():
        raise ValueError(
            f"Arquivo temporário da sessão {session_id} não está mais disponível."
        )

    # 4. Atomically claim the reprocess (failed -> pending)
    claimed = store.try_claim_reprocess(session_id)
    if claimed is None:
        raise ValueError(
            f"Sessão {session_id} já foi reivindicada por outra retentativa."
        )

    # 5. Schedule background processing — protect against task creation failure
    coroutine = _process_document(session_id)
    try:
        asyncio.create_task(coroutine)
    except Exception:
        # Task creation failed: close coroutine and restore failed status
        coroutine.close()
        session = store.get(session_id)
        if session is not None:
            session.status = "failed"
            store.update(session)
        raise


def discard_session(session_id: str) -> None:
    """Discard a failed OCR session, removing it from the store and deleting the temp file.

    Atomically removes the session under lock, then deletes the file outside the lock.

    Args:
        session_id: The session to discard.

    Raises:
        ValueError: If session doesn't exist or isn't in 'failed' status.
    """
    # 1-4. Under lock: verify existence, status, capture file_path, remove session
    with store.lock:
        session = store._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Sessão {session_id} não encontrada.")

        if session.status != "failed":
            raise ValueError(
                f"Sessão {session_id} está em estado '{session.status}', "
                f"não 'failed'. Descarte só é possível após falha."
            )

        file_path = session.file_path
        store._sessions.pop(session_id, None)

    # 5-6. Outside lock: delete the physical file
    if file_path:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info("Deleted OCR temp file on discard: %s", file_path)
        except OSError as exc:
            logger.warning(
                "Failed to delete OCR temp file on discard %s: %s", file_path, exc
            )


def session_to_status_response(session: OCRSession) -> dict:
    """Convert OCRSession to StatusResponse dict.

    Includes financial indicators (D-17) when the session has completed OCR:
    - extracted_total: calculated from all original items when status is 'completed' or 'confirming'.
    - launched_total: None before confirmation (only available in ConfirmImportResponse).
    - items_without_subtotal_count: count of items without available subtotal.
    """
    response: dict = {
        "session_id": session.session_id,
        "status": session.status,
        "document_total": session.document_total,
        "purchased_at": session.purchased_at,
        "access_key": session.access_key,
        "items": [item.model_dump() for item in session.items],
        "document_discounts": [d.model_dump() for d in session.document_discounts],
        "error": session.error,
        "model_used": session.model_used,
        # Financial indicators are None/0 by default.
        "extracted_total": None,
        "launched_total": None,
        "items_without_subtotal_count": 0,
    }

    # Calculate extracted_total when OCR has completed and items are available.
    if session.status in ("completed", "confirming") and session.items:
        extracted_total, without_subtotal = _calculate_extracted_total(session)
        response["extracted_total"] = extracted_total
        response["items_without_subtotal_count"] = without_subtotal

    # launched_total is only available after confirmation (in ConfirmImportResponse).
    # Before confirmation, it remains None.

    return response


# ─── Confirmação de importação (Etapa 3) ────────────────────────────────


def _validate_access_key(value: str | None) -> str:
    """Validate access_key: exactly 44 ASCII digits.

    Returns the validated key or raises BusinessRuleError.
    """
    if value is None:
        raise BusinessRuleError(
            "A chave de acesso é obrigatória para confirmação de importação."
        )
    value = value.strip()
    if not value:
        raise BusinessRuleError(
            "A chave de acesso é obrigatória para confirmação de importação."
        )
    if not (len(value) == 44 and all(c in "0123456789" for c in value)):
        raise BusinessRuleError(
            "A chave de acesso deve conter exatamente 44 dígitos numéricos."
        )
    return value


def _build_original_item_map(session: OCRSession) -> dict[str, OCRItem]:
    """Build a map of original OCR items by item_id."""
    return {item.item_id: item for item in session.items}


def _validate_items_coverage(
    original_map: dict[str, OCRItem],
    request: ConfirmImportRequest,
) -> None:
    """Validate that every original item appears exactly once across
    confirmed_items and excluded_item_ids, with no overlap or omission.
    """
    confirmed_ids = {ci.item_id for ci in request.confirmed_items}
    excluded_ids = set(request.excluded_item_ids)
    original_ids = set(original_map.keys())

    # Check for non-existent IDs
    all_referenced = confirmed_ids | excluded_ids
    unknown = all_referenced - original_ids
    if unknown:
        raise BusinessRuleError(
            f"Identificador(es) de item inexistente(s): {', '.join(sorted(unknown))}."
        )

    # Check for overlap between confirmed and excluded
    overlap = confirmed_ids & excluded_ids
    if overlap:
        raise BusinessRuleError(
            f"Item(ns) não podem estar simultaneamente confirmados e excluídos: "
            f"{', '.join(sorted(overlap))}."
        )

    # Check for omitted items
    omitted = original_ids - all_referenced
    if omitted:
        raise BusinessRuleError(
            f"Item(ns) original(is) não contemplado(s): {', '.join(sorted(omitted))}."
        )


def _validate_lots_conservation(
    confirmed_item: Any,  # ConfirmedItem from schema
    original_item: OCRItem,
) -> None:
    """Validate lot quantity conservation in base units (D-11).

    When an item is split into lots, the sum of converted quantities must
    exactly equal the original quantity in base units.
    """
    if not confirmed_item.lots:
        return

    # Original quantity in base units
    if original_item.quantity is None or original_item.conversion_factor is None:
        raise BusinessRuleError(
            f"Item {confirmed_item.item_id}: dados originais insuficientes "
            f"para validar conservação de lotes."
        )
    original_base_qty = original_item.quantity * original_item.conversion_factor

    # Sum of lot quantities in base units
    sum_base_qty = Decimal("0")
    for lot in confirmed_item.lots:
        sum_base_qty += lot.commercial_quantity * lot.conversion_factor

    if original_base_qty != sum_base_qty:
        raise BusinessRuleError(
            f"Item {confirmed_item.item_id}: a soma das quantidades dos lotes "
            f"em unidade-base ({sum_base_qty}) não corresponde à quantidade "
            f"original ({original_base_qty})."
        )


def _calculate_lot_price(
    item_price: Decimal,
    item_factor: Decimal,
    lot_factor: Decimal,
) -> Decimal:
    """Calculate lot price from item price and conversion factors.

    lot_price = item_price × (lot_factor / item_factor)
    """
    return (item_price * lot_factor / item_factor).quantize(Decimal("0.01"))


def _build_create_draft(
    session: OCRSession,
    request: ConfirmImportRequest,
    access_key: str,
) -> CreateDraft:
    """Build a CreateDraft from the confirmed items.

    Expands lots into individual CreateDraftItem entries.
    Calculates lot prices from item prices and conversion factors.
    Transports discounts from OCR items and document discounts.
    """
    purchased_at: datetime | None = None
    if session.purchased_at is not None:
        purchased_at = session.purchased_at

    # Build original item map for discount lookup
    original_map = {item.item_id: item for item in session.items}

    draft_items: list[CreateDraftItem] = []

    for confirmed in request.confirmed_items:
        # Get discounts from original OCR item
        original = original_map.get(confirmed.item_id)
        item_discounts: list[ItemDiscount] | None = None
        if original and original.discounts:
            item_discounts = [
                ItemDiscount(
                    value=d.value,
                    nature=d.nature,
                    description=d.description,
                )
                for d in original.discounts
            ]

        if confirmed.lots:
            # Expand lots into individual draft items
            for lot in confirmed.lots:
                lot_price = _calculate_lot_price(
                    confirmed.commercial_unit_price,
                    confirmed.conversion_factor,
                    lot.conversion_factor,
                )
                draft_items.append(
                    CreateDraftItem(
                        product_id=confirmed.product_id,
                        commercial_unit=lot.commercial_unit,
                        conversion_factor=lot.conversion_factor,
                        commercial_quantity=lot.commercial_quantity,
                        commercial_unit_price=lot_price,
                        expiry_date=lot.expiry_date,
                        item_discounts=item_discounts,
                    )
                )
        else:
            # Single item without lot split
            draft_items.append(
                CreateDraftItem(
                    product_id=confirmed.product_id,
                    commercial_unit=confirmed.commercial_unit,
                    conversion_factor=confirmed.conversion_factor,
                    commercial_quantity=confirmed.commercial_quantity,
                    commercial_unit_price=confirmed.commercial_unit_price,
                    expiry_date=confirmed.expiry_date,
                    item_discounts=item_discounts,
                )
            )

    # Transport document discounts from OCR session
    document_discounts: list[DocumentDiscountCreate] | None = None
    if session.document_discounts:
        document_discounts = [
            DocumentDiscountCreate(
                value=d.value or Decimal("0"),
                nature=d.nature,
                description=d.description,
            )
            for d in session.document_discounts
        ]

    return CreateDraft(
        purchased_at=purchased_at,
        access_key=access_key,
        items=draft_items,
        document_discounts=document_discounts,
    )


def _calculate_extracted_total(session: OCRSession) -> tuple[Decimal | None, int]:
    """Calculate extracted_total from ALL original items (including excluded).

    Returns (total, items_without_subtotal_count).

    Priority: subtotal_printed → subtotal_calculated → quantity × price.
    Zero is a valid subtotal.
    """
    total = Decimal("0")
    without_subtotal = 0

    for item in session.items:
        subtotal: Decimal | None = None

        # Priority 1: subtotal_printed
        if item.subtotal_printed is not None:
            subtotal = item.subtotal_printed

        # Priority 2: subtotal_calculated
        elif item.subtotal_calculated is not None:
            subtotal = item.subtotal_calculated

        # Priority 3: quantity × commercial_unit_price
        elif (
            item.quantity is not None
            and item.commercial_unit_price is not None
        ):
            subtotal = item.quantity * item.commercial_unit_price

        if subtotal is not None:
            total += subtotal
        else:
            without_subtotal += 1

    return total, without_subtotal


def _calculate_launched_total(request: ConfirmImportRequest) -> Decimal:
    """Calculate launched_total from confirmed items only.

    For items with lots: Σ(lot.qty × lot.price)
    For items without lots: qty × price
    """
    total = Decimal("0")

    for confirmed in request.confirmed_items:
        if confirmed.lots:
            for lot in confirmed.lots:
                lot_price = _calculate_lot_price(
                    confirmed.commercial_unit_price,
                    confirmed.conversion_factor,
                    lot.conversion_factor,
                )
                total += lot.commercial_quantity * lot_price
        else:
            total += confirmed.commercial_quantity * confirmed.commercial_unit_price

    return total


def _copy_to_permanent_storage(
    session: OCRSession,
    purchase_id: int,
) -> str | None:
    """Copy the temporary OCR file to permanent purchase storage.

    Returns the relative path (e.g. "purchases/123_abc.jpg") or None if
    the temp file is not available.

    The permanent file is named {purchase_id}_{session_id}.{ext}.

    If shutil.copy2() fails, the destination file is removed (if partially
    created) and the exception is propagated. The source temp file is preserved.
    """
    if not session.file_path or not Path(session.file_path).exists():
        return None

    src = Path(session.file_path)
    dest_dir = settings.entity_upload_path("purchases")
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Derive extension from the temp file
    ext = src.suffix or ".jpg"
    dest_name = f"{purchase_id}_{session.session_id}{ext}"
    dest = dest_dir / dest_name

    try:
        shutil.copy2(str(src), str(dest))
    except Exception:
        # Remove partially created destination file to avoid orphans
        if dest.exists():
            try:
                dest.unlink()
            except OSError:
                pass
        raise

    # Return relative path for document_path storage
    return f"purchases/{dest_name}"


def confirm_import(
    db: Session,
    session_id: str,
    request: ConfirmImportRequest,
) -> ConfirmImportResponse:
    """Confirm an OCR import and create a DRAFT purchase.

    This function:
    1. Claims the session atomically (completed → confirming).
    2. Validates the access key (44 ASCII digits).
    3. Validates item coverage (all original items represented exactly once).
    4. Validates lot quantity conservation.
    5. Copies the temp file to permanent storage (if available).
    6. Builds CreateDraft from confirmed items with discounts.
    7. Calls create_draft() to create the DRAFT purchase.
    8. Calculates totals.

    The caller (endpoint) is responsible for:
    - db.commit() after success
    - db.rollback() on failure
    - Deleting the temp file after successful commit
    - Restoring session to 'completed' on pre-commit failure
    - Removing session after successful commit

    Raises:
        BusinessRuleError: On validation failures or business rule violations.
    """
    # 1. Claim session atomically
    session = store.try_claim_confirming(session_id)
    if session is None:
        raise BusinessRuleError(
            "Sessão não encontrada ou não disponível para confirmação."
        )

    # 2. Validate access key
    access_key = _validate_access_key(session.access_key)

    # 3. Build original item map and validate coverage
    original_map = _build_original_item_map(session)
    _validate_items_coverage(original_map, request)

    # 4. Validate lot conservation for each confirmed item
    for confirmed in request.confirmed_items:
        original = original_map.get(confirmed.item_id)
        if original is not None:
            _validate_lots_conservation(confirmed, original)

    # 5. Copy temp file to permanent storage (before draft creation)
    #    This must happen before create_draft so document_path can be set.
    #    For OCR imports, missing document prevents draft creation.
    document_path = _copy_to_permanent_storage(session, 0)
    if document_path is None:
        raise BusinessRuleError(
            "O documento original não está mais disponível para cópia permanente."
        )

    # 6. Build CreateDraft with document_path and discounts
    draft_data = _build_create_draft(session, request, access_key)
    draft_data.document_path = document_path

    # 7. Create DRAFT purchase (does NOT commit — caller responsibility)
    purchase_read = _create_draft(db, draft_data)

    # 8. Calculate totals
    extracted_total, items_without_subtotal = _calculate_extracted_total(session)
    launched_total = _calculate_launched_total(request)

    totals = ConfirmImportTotals(
        extracted_total=extracted_total,
        launched_total=launched_total,
        items_without_subtotal_count=items_without_subtotal,
    )

    # 9. Build response
    confirmed_reads: list[ConfirmedItemRead] = []
    for confirmed in request.confirmed_items:
        confirmed_reads.append(
            ConfirmedItemRead(
                item_id=confirmed.item_id,
                product_id=confirmed.product_id,
                commercial_unit=confirmed.commercial_unit,
                conversion_factor=confirmed.conversion_factor,
                commercial_quantity=confirmed.commercial_quantity,
                commercial_unit_price=confirmed.commercial_unit_price,
                expiry_date=confirmed.expiry_date,
                lots=confirmed.lots,
            )
        )

    excluded_reads: list[ExcludedItemRead] = []
    for exc_id in request.excluded_item_ids:
        original = original_map.get(exc_id)
        excluded_reads.append(
            ExcludedItemRead(
                item_id=exc_id,
                description=original.description if original else None,
            )
        )

    return ConfirmImportResponse(
        purchase_id=purchase_read.id,
        purchased_at=purchase_read.purchased_at,
        access_key=purchase_read.access_key,
        status=purchase_read.status,
        confirmed_items=confirmed_reads,
        excluded_items=excluded_reads,
        totals=totals,
    )
