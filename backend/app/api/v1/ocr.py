"""OCR API router for M13.

Endpoints:
- POST /ocr/upload — Upload document for OCR processing
- GET /ocr/{session_id}/status — Poll session status and results
- POST /ocr/{session_id}/confirm — Confirm OCR import and create purchase
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.service import security
from app.core.database import get_db
from app.core.exceptions import BusinessRuleError
from app.ocr.schemas import ConfirmImportRequest, ConfirmImportResponse, StatusResponse, UploadResponse
from app.ocr.service import (
    _copy_to_permanent_storage,
    confirm_import,
    discard_session,
    get_session,
    reprocess_document,
    session_to_status_response,
    upload_document,
)
from app.ocr.state import store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ocr", tags=["ocr"])

bearer = HTTPBearer()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_endpoint(
    file: UploadFile,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> UploadResponse:
    """Upload a purchase document for OCR processing.

    Accepts JPEG, PNG, and WebP images (D-14).
    Returns immediately with session_id; processing runs in background (D-1).
    Requires JWT authentication (D-15).
    """
    # Validate JWT token — decode to verify it's valid
    from app.auth.utils import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    try:
        session = upload_document(file)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return UploadResponse(
        session_id=session.session_id,
        status=session.status,
    )


@router.get("/{session_id}/status", response_model=StatusResponse)
async def get_status_endpoint(
    session_id: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> StatusResponse:
    """Get OCR session status and results via polling.

    Returns current status: pending, processing, completed, or failed.
    When completed, returns extracted items and data.
    Requires JWT authentication (D-15).
    """
    # Validate JWT token
    from app.auth.utils import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    session = get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada",
        )

    return StatusResponse(**session_to_status_response(session))


@router.post(
    "/{session_id}/confirm",
    response_model=ConfirmImportResponse,
    status_code=status.HTTP_200_OK,
)
def confirm_import_endpoint(
    session_id: str,
    request: ConfirmImportRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> ConfirmImportResponse:
    """Confirm an OCR import and create a DRAFT purchase.

    Transactional flow:
    1. Call confirm_import() — validates, copies document to permanent storage,
       and creates the DRAFT purchase (no commit).
    2. db.commit() — persists the DRAFT purchase.
    3. Delete the temp file after successful commit.
    4. Remove the session from memory.

    On pre-commit failure:
    - db.rollback() is executed.
    - The permanent document file (if created) is deleted to avoid orphans.
    - Session is restored to 'completed' so the operator can retry.

    On post-commit failure (session cleanup):
    - The purchase remains committed — no logical rollback.
    - Session is NOT restored to 'completed' — a second confirmation is impossible.

    Requires JWT authentication (D-15).
    """
    from app.auth.utils import decode_token

    # Validate JWT token
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    # Capture session before confirm_import changes its state
    session_before = store.get(session_id)
    temp_file_path = session_before.file_path if session_before else None

    try:
        # Step 1: Call service — validates, copies document, creates DRAFT (no commit)
        response = confirm_import(db, session_id, request)

        # Step 2: Commit the transaction
        db.commit()

    except BusinessRuleError as exc:
        # Pre-commit business rule violation — rollback and cleanup
        db.rollback()
        # Delete orphan permanent file if it was created
        _cleanup_orphan_permanent_file(session_id)
        store.restore_completed(session_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except IntegrityError as exc:
        # Pre-commit integrity violation — rollback and cleanup
        db.rollback()
        # Delete orphan permanent file if it was created
        _cleanup_orphan_permanent_file(session_id)
        store.restore_completed(session_id)

        # Check if it's the access_key unique constraint
        if hasattr(exc, "orig") and hasattr(exc.orig, "diag"):
            constraint_name = getattr(exc.orig.diag, "constraint_name", None)
            if constraint_name == "uq_purchases_access_key":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Esta chave de acesso de NF-e já está cadastrada.",
                ) from exc

        # Other integrity errors — return generic database error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Erro de integridade no banco de dados.",
        ) from exc

    except Exception as exc:
        # Any other pre-commit failure — rollback and cleanup
        db.rollback()
        # Delete orphan permanent file if it was created
        _cleanup_orphan_permanent_file(session_id)
        store.restore_completed(session_id)
        logger.error(
            "Unexpected error during confirmation of session %s: %s",
            session_id,
            str(exc),
            exc_info=exc,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno durante a confirmação.",
        ) from exc

    # Step 3: Post-commit cleanup — delete temp file and remove session
    # If this fails, the purchase is already committed and cannot be rolled back.
    try:
        # Delete the temporary OCR file — permanent copy is already in place
        if temp_file_path:
            _delete_file_silent(temp_file_path)
    except Exception as exc:
        logger.warning(
            "Failed to delete temp file %s after commit: %s",
            temp_file_path, exc,
        )

    try:
        store.remove(session_id)
    except Exception as exc:
        logger.error(
            "Failed to remove session %s after commit: %s",
            session_id,
            str(exc),
            exc_info=exc,
        )
        # Do NOT restore session — purchase is committed, confirmation is done.

    return response


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
        logger.warning("Failed to delete file %s: %s", file_path, exc)


def _cleanup_orphan_permanent_file(session_id: str) -> None:
    """Delete orphan permanent file created by _copy_to_permanent_storage.

    The permanent file is named {purchase_id}_{session_id}.{ext}.
    Since we don't know the purchase_id yet (commit failed), we search
    for files matching the session_id pattern.
    """
    from app.core.config import settings

    purchases_dir = settings.entity_upload_path("purchases")
    if not purchases_dir.exists():
        return

    try:
        for file_path in purchases_dir.iterdir():
            if file_path.is_file() and session_id in file_path.name:
                file_path.unlink()
                logger.info(
                    "Deleted orphan permanent file: %s", file_path
                )
    except OSError as exc:
        logger.warning(
            "Failed to cleanup orphan permanent files for session %s: %s",
            session_id, exc,
        )


@router.post("/{session_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_endpoint(
    session_id: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> None:
    """Retry OCR processing for a failed session.

    Re-schedules background processing using the preserved temp file.
    Returns 202 when the task is scheduled.
    Returns 404 if the session doesn't exist.
    Returns 409 if the session is not in 'failed' status, the file is unavailable,
    or another request already claimed the session.

    Requires JWT authentication.
    """
    # Validate JWT token
    from app.auth.utils import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    try:
        reprocess_document(session_id)
    except ValueError as exc:
        error_msg = str(exc).lower()
        if "não encontrada" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        # Wrong status, missing file, or already claimed by another request
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def discard_endpoint(
    session_id: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> Response:
    """Discard a failed OCR session, removing it and deleting the temp file.

    Returns 204 on success.
    Returns 404 if the session doesn't exist.
    Returns 409 if the session is not in 'failed' status.

    Requires JWT authentication.
    """
    # Validate JWT token
    from app.auth.utils import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    try:
        discard_session(session_id)
    except ValueError as exc:
        error_msg = str(exc).lower()
        if "não encontrada" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        # Wrong status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{session_id}/preview")
def preview_document_endpoint(
    session_id: str,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
) -> FileResponse:
    """Preview the uploaded document image for the comprovante tab.

    Returns the original uploaded file so the operator can verify the OCR results.
    Returns 404 if the session doesn't exist or the file is unavailable.

    Requires JWT authentication.
    """
    from app.auth.utils import decode_token

    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )

    session = get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada",
        )

    if not session.file_path or not Path(session.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não disponível",
        )

    return FileResponse(
        path=session.file_path,
        media_type=session.file_mime_type or "image/jpeg",
    )
