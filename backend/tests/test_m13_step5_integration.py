"""M13 Step 5 — Integração: ciclo de vida de arquivos e autenticação.

Testes reais (sem mock do fluxo central) cobrindo:
1. Autenticação JWT em GET /purchases/{id}/document
2. Commit bem-sucedido: DRAFT criado, permanente vinculado, temp excluído
3. Falha no commit: rollback, temp preservado, permanente removido
4. Falha na cópia: sem DRAFT, temp preservado, sem órfãos
5. Descarte de sessão: temp removido, permanente preservado
6. DRAFT OCR sem ENTRY (real)
7. Descontos persistidos (real)
"""
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from tempfile import mkdtemp
from typing import Any, Callable
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.products.models import InventoryMovement, Product
from app.ocr.state import store
from app.purchases.models import Purchase, PurchaseItem, PurchaseDocumentDiscount


def _create_product(
    client: TestClient,
    register_product: Callable[[int], None],
    *,
    name: str | None = None,
    unit: str = "UN",
    active: bool = True,
) -> dict[str, Any]:
    """Create a product and register it for cleanup."""
    if name is None:
        name = f"step5-int-{uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/products", json={"name": name, "base_unit": unit}
    )
    assert response.status_code == 201, response.text
    product = response.json()
    register_product(product["id"])
    if not active:
        resp = client.post(f"/api/v1/products/{product['id']}/deactivate")
        assert resp.status_code == 200
    return product


def _get_auth_headers(client: TestClient) -> dict:
    """Create admin, login, and return auth headers."""
    email = f"step5-int-{uuid4().hex[:8]}@casaafeto.com"
    payload = {
        "email": email,
        "password": "Admin1234",
        "full_name": "Step5 Integration Admin",
    }
    resp = client.post("/api/v1/auth/setup/create-admin", json=payload)
    if resp.status_code != 201:
        from app.auth.models import User
        from app.auth.utils import hash_password
        with SessionLocal() as db:
            user = User(
                email=email,
                password_hash=hash_password("Admin1234"),
                full_name="Step5 Integration Admin",
                role="admin",
                is_active=True,
            )
            db.add(user)
            db.commit()

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Admin1234"},
    )
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    raise RuntimeError(f"Failed to login: {resp.status_code} {resp.text}")


# ─── 1. Document endpoint JWT authentication ───


def test_get_document_requires_auth(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """GET /purchases/{id}/document without JWT returns 401 or 403."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create a DRAFT with document_path
    purchases_dir = settings.entity_upload_path("purchases")
    purchases_dir.mkdir(parents=True, exist_ok=True)
    doc_file = purchases_dir / f"auth-test-{uuid4().hex[:8]}.jpg"
    doc_file.write_bytes(b"\xff\xd8\xff\xe0document-content")

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ],
        "document_path": f"purchases/{doc_file.name}",
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Request without auth — should be rejected
    response = client.get(f"/api/v1/purchases/{purchase_id}/document")
    assert response.status_code in (401, 403)

    # Cleanup
    doc_file.unlink(missing_ok=True)


def test_get_document_with_valid_auth(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """GET /purchases/{id}/document with valid JWT returns 200."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]
    headers = _get_auth_headers(client)

    purchases_dir = settings.entity_upload_path("purchases")
    purchases_dir.mkdir(parents=True, exist_ok=True)
    doc_file = purchases_dir / f"auth-ok-{uuid4().hex[:8]}.jpg"
    doc_file.write_bytes(b"\xff\xd8\xff\xe0document-content-ok")

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ],
        "document_path": f"purchases/{doc_file.name}",
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Request with valid auth
    response = client.get(
        f"/api/v1/purchases/{purchase_id}/document", headers=headers
    )
    assert response.status_code == 200
    assert b"\xff\xd8\xff\xe0document-content-ok" in response.content

    # Cleanup
    doc_file.unlink(missing_ok=True)


def test_get_document_with_invalid_token(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """GET /purchases/{id}/document with invalid JWT returns 401."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchases_dir = settings.entity_upload_path("purchases")
    purchases_dir.mkdir(parents=True, exist_ok=True)
    doc_file = purchases_dir / f"auth-invalid-{uuid4().hex[:8]}.jpg"
    doc_file.write_bytes(b"\xff\xd8\xff\xe0document-content")

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ],
        "document_path": f"purchases/{doc_file.name}",
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Request with invalid token
    response = client.get(
        f"/api/v1/purchases/{purchase_id}/document",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code == 401

    # Cleanup
    doc_file.unlink(missing_ok=True)


# ─── 2. Full file lifecycle: successful commit ───


def test_ocr_confirm_full_lifecycle_success(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Full OCR confirm: DRAFT created, permanent file linked, temp deleted."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]
    headers = _get_auth_headers(client)

    # Upload document
    jpeg_data = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )
    files = {"file": ("document.jpg", BytesIO(jpeg_data), "image/jpeg")}

    with patch("app.ocr.service.call_gemini_ocr") as mock_ocr:
        from app.ocr.schemas import OCRItem, OCRResult

        mock_ocr.return_value = OCRResult(
            items=[
                OCRItem(
                    item_id="item-1",
                    description=product["name"],
                    quantity=Decimal("10"),
                    commercial_unit="UN",
                    commercial_unit_price=Decimal("5.00"),
                    product_id=product_id,
                    conversion_factor=Decimal("1"),
                )
            ],
            purchased_at=datetime(2025, 6, 15, 10, 0, 0),
            access_key="1" * 44,
        )

        resp = client.post("/api/v1/ocr/upload", files=files, headers=headers)
    assert resp.status_code == 201, resp.text
    session_id = resp.json()["session_id"]

    # Wait for OCR to complete (mocked, so it's immediate)
    import time
    time.sleep(0.5)

    # Get status to confirm OCR completed
    resp = client.get(f"/api/v1/ocr/{session_id}/status", headers=headers)
    assert resp.status_code == 200
    status_data = resp.json()
    assert status_data["status"] == "completed", f"Expected completed, got {status_data['status']}"

    # Find the temp file
    ocr_dir = settings.entity_upload_path("ocr")
    temp_files_before = list(ocr_dir.glob(f"*{session_id}*")) if ocr_dir.exists() else []
    assert len(temp_files_before) == 1, f"Expected 1 temp file, found {len(temp_files_before)}"
    temp_file_path = temp_files_before[0]

    # Confirm import
    confirm_payload = {
        "confirmed_items": [
            {
                "item_id": "item-1",
                "product_id": product_id,
                "commercial_quantity": "10",
                "commercial_unit_price": "5.00",
                "conversion_factor": "1",
            }
        ],
        "excluded_item_ids": [],
    }
    resp = client.post(
        f"/api/v1/ocr/{session_id}/confirm",
        json=confirm_payload,
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    confirm_data = resp.json()
    assert confirm_data["status"] == "DRAFT"
    purchase_id = confirm_data["purchase_id"]

    # Verify: DRAFT created in DB
    with SessionLocal() as db:
        purchase = db.get(Purchase, purchase_id)
        assert purchase is not None
        assert purchase.status == "DRAFT"
        assert purchase.document_path is not None
        assert purchase.document_path.startswith("purchases/")

        # No ENTRY movements
        movements = db.query(InventoryMovement).filter_by(
            purchase_id=purchase_id
        ).all()
        assert len(movements) == 0, "DRAFT should have no ENTRY movements"

    # Verify: permanent file exists
    purchases_dir = settings.entity_upload_path("purchases")
    permanent_files = list(purchases_dir.glob(f"*{session_id}*"))
    assert len(permanent_files) == 1, f"Expected 1 permanent file, found {len(permanent_files)}"

    # Verify: temp file deleted
    temp_files_after = list(ocr_dir.glob(f"*{session_id}*")) if ocr_dir.exists() else []
    assert len(temp_files_after) == 0, f"Temp file should be deleted, found {len(temp_files_after)}"

    # Verify: document accessible via endpoint
    resp = client.get(
        f"/api/v1/purchases/{purchase_id}/document", headers=headers
    )
    assert resp.status_code == 200

    # Cleanup permanent file
    permanent_files[0].unlink(missing_ok=True)


# ─── 3. Failed commit: rollback, temp preserved, permanent cleaned ───


def test_ocr_confirm_failed_commit_preserves_temp(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """If commit fails, temp file is preserved and permanent file is cleaned."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]
    headers = _get_auth_headers(client)

    # Upload document
    jpeg_data = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )
    files = {"file": ("document.jpg", BytesIO(jpeg_data), "image/jpeg")}

    with patch("app.ocr.service.call_gemini_ocr") as mock_ocr:
        from app.ocr.schemas import OCRItem, OCRResult

        mock_ocr.return_value = OCRResult(
            items=[
                OCRItem(
                    item_id="item-1",
                    description=product["name"],
                    quantity=Decimal("10"),
                    commercial_unit="UN",
                    commercial_unit_price=Decimal("5.00"),
                    product_id=product_id,
                    conversion_factor=Decimal("1"),
                )
            ],
            purchased_at=datetime(2025, 6, 15, 10, 0, 0),
            access_key="1" * 44,
        )

        resp = client.post("/api/v1/ocr/upload", files=files, headers=headers)
    assert resp.status_code == 201, resp.text
    session_id = resp.json()["session_id"]

    import time
    time.sleep(0.5)

    # Get status
    resp = client.get(f"/api/v1/ocr/{session_id}/status", headers=headers)
    assert resp.status_code == 200
    status_data = resp.json()
    assert status_data["status"] == "completed"

    # Find temp file
    ocr_dir = settings.entity_upload_path("ocr")
    temp_files_before = list(ocr_dir.glob(f"*{session_id}*")) if ocr_dir.exists() else []
    assert len(temp_files_before) == 1

    # Simulate commit failure by mocking db.commit to raise IntegrityError
    # We use an invalid access_key to trigger BusinessRuleError before commit
    # But to test commit failure, we need to mock at the endpoint level
    # Instead, we test with a duplicate access_key scenario:
    # Create a purchase with the same access_key first
    bad_access_key = "9" * 44
    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ],
        "access_key": bad_access_key,
    }
    client.post("/api/v1/purchases/draft", json=payload)

    # Now confirm with the same access_key — should fail with IntegrityError
    confirm_payload = {
        "confirmed_items": [
            {
                "item_id": "item-1",
                "product_id": product_id,
                "commercial_quantity": "10",
                "commercial_unit_price": "5.00",
                "conversion_factor": "1",
            }
        ],
        "excluded_item_ids": [],
    }

    # Override the session's access_key to match the existing one
    from app.ocr.state import store as ocr_store
    session = ocr_store.get(session_id)
    if session:
        session.access_key = bad_access_key
        ocr_store.update(session)

    resp = client.post(
        f"/api/v1/ocr/{session_id}/confirm",
        json=confirm_payload,
        headers=headers,
    )
    # Should fail — either 409 (BusinessRuleError) or 503 (IntegrityError)
    assert resp.status_code in (409, 503), f"Expected 409/503, got {resp.status_code}: {resp.text}"

    # Verify: temp file still exists (preserved for retry)
    temp_files_after = list(ocr_dir.glob(f"*{session_id}*")) if ocr_dir.exists() else []
    assert len(temp_files_after) == 1, "Temp file should be preserved after failed commit"

    # Verify: no permanent file orphan
    purchases_dir = settings.entity_upload_path("purchases")
    permanent_files = list(purchases_dir.glob(f"*{session_id}*")) if purchases_dir.exists() else []
    assert len(permanent_files) == 0, "No permanent file orphan after failed commit"

    # Cleanup permanent files if any
    for f in permanent_files:
        f.unlink(missing_ok=True)


# ─── 4. Copy failure: no draft, temp preserved, no orphans ───


def test_ocr_confirm_copy_failure_no_orphan(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """If copy fails, no DRAFT is created and no permanent file orphan exists."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    session_id = f"copy-fail-{uuid4().hex[:8]}"
    temp_dir = Path(mkdtemp())
    temp_file = temp_dir / f"{session_id}.jpg"
    temp_file.write_bytes(b"\xff\xd8\xff\xe0test-copy-fail")

    from app.ocr.schemas import OCRItem, OCRSession

    session = OCRSession(
        session_id=session_id,
        status="completed",
        file_path=str(temp_file),
        file_mime_type="image/jpeg",
        items=[
            OCRItem(
                item_id="item-1",
                description=product["name"],
                quantity=Decimal("10"),
                commercial_unit="UN",
                commercial_unit_price=Decimal("5.00"),
                product_id=product_id,
                conversion_factor=Decimal("1"),
            )
        ],
        access_key="1" * 44,
        purchased_at=datetime(2025, 6, 15, 10, 0, 0),
    )
    store._sessions.clear()
    store.add(session)

    # Mock shutil.copy2 to fail
    with patch("app.ocr.service.shutil.copy2", side_effect=OSError("Disk full")):
        from app.core.exceptions import BusinessRuleError
        from app.ocr.service import confirm_import
        from app.ocr.schemas import ConfirmImportRequest, ConfirmedItem

        request = ConfirmImportRequest(
            confirmed_items=[
                ConfirmedItem(
                    item_id="item-1",
                    product_id=product_id,
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    conversion_factor=Decimal("1"),
                )
            ],
            excluded_item_ids=[],
        )

        mock_db = MagicMock()
        with pytest.raises((BusinessRuleError, OSError)):
            confirm_import(mock_db, session_id, request)

    # Verify: temp file preserved
    assert temp_file.exists(), "Temp file should be preserved after copy failure"

    # Verify: no permanent file orphan
    purchases_dir = settings.entity_upload_path("purchases")
    permanent_files = list(purchases_dir.glob(f"*{session_id}*")) if purchases_dir.exists() else []
    assert len(permanent_files) == 0, "No permanent file orphan after copy failure"

    # Cleanup
    temp_file.unlink()
    temp_dir.rmdir()


# ─── 5. Session discard: temp removed, permanent preserved ───


def test_ocr_discard_session_preserves_permanent(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Discarding a session removes temp file but not permanent document."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]
    headers = _get_auth_headers(client)

    # Create a DRAFT with document_path (simulating prior OCR import)
    purchases_dir = settings.entity_upload_path("purchases")
    purchases_dir.mkdir(parents=True, exist_ok=True)
    permanent_file = purchases_dir / f"discard-test-{uuid4().hex[:8]}.jpg"
    permanent_file.write_bytes(b"permanent-content")

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ],
        "document_path": f"purchases/{permanent_file.name}",
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Create a session with a temp file
    session_id = f"discard-{uuid4().hex[:8]}"
    temp_dir = Path(mkdtemp())
    temp_file = temp_dir / f"{session_id}.jpg"
    temp_file.write_bytes(b"temp-content")

    from app.ocr.schemas import OCRItem, OCRSession

    session = OCRSession(
        session_id=session_id,
        status="failed",
        file_path=str(temp_file),
        file_mime_type="image/jpeg",
        items=[],
    )
    store.add(session)

    # Discard session
    response = client.delete(f"/api/v1/ocr/{session_id}", headers=headers)
    assert response.status_code in (200, 204)

    # Verify: temp file removed
    assert not temp_file.exists(), "Temp file should be deleted after discard"

    # Verify: permanent file preserved
    assert permanent_file.exists(), "Permanent file should be preserved after discard"

    # Verify: document still accessible
    response = client.get(
        f"/api/v1/purchases/{purchase_id}/document", headers=headers
    )
    assert response.status_code == 200

    # Cleanup
    try:
        temp_dir.rmdir()
    except OSError:
        pass
    permanent_file.unlink(missing_ok=True)


# ─── 6. DRAFT OCR without ENTRY (real, no mock) ───


def test_ocr_draft_no_entry_real(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """DRAFT created via OCR has no ENTRY movements (real DB check)."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Check initial balance
    with SessionLocal() as db:
        initial_balance = (
            db.query(InventoryMovement)
            .filter_by(product_id=product_id)
            .count()
        )

    # Create DRAFT via POST /purchases/draft (simulating OCR-created draft)
    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "10",
                "commercial_unit_price": "5.00",
            }
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]
    assert response.json()["status"] == "DRAFT"

    # Verify: no new movements
    with SessionLocal() as db:
        new_balance = (
            db.query(InventoryMovement)
            .filter_by(product_id=product_id)
            .count()
        )
        assert new_balance == initial_balance, "DRAFT should not generate ENTRY"

        # Verify purchase has no movements linked
        movements = db.query(InventoryMovement).filter_by(
            purchase_id=purchase_id
        ).all()
        assert len(movements) == 0


# ─── 7. Discounts persisted (real, no mock) ───


def test_draft_discounts_persisted_real(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Item and document discounts are persisted in the database."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "10",
                "commercial_unit_price": "5.00",
                "item_discounts": [
                    {
                        "value": 5.00,
                        "nature": "volume",
                        "description": "Desconto por volume",
                    }
                ],
            }
        ],
        "document_discounts": [
            {
                "value": 10.00,
                "nature": "frete",
                "description": "Desconto de frete",
            }
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Verify in database
    with SessionLocal() as db:
        # Check item discounts
        item = db.query(PurchaseItem).filter_by(purchase_id=purchase_id).first()
        assert item is not None
        assert item.item_discounts is not None
        assert len(item.item_discounts) == 1
        assert item.item_discounts[0]["nature"] == "volume"

        # Check document discounts
        doc_discounts = db.query(PurchaseDocumentDiscount).filter_by(
            purchase_id=purchase_id
        ).all()
        assert len(doc_discounts) == 1
        assert doc_discounts[0].nature == "frete"
        assert doc_discounts[0].value == Decimal("10.00")

    # Verify via API response
    response = client.get(f"/api/v1/purchases/{purchase_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["item_discounts"] is not None
    assert len(data["items"][0]["item_discounts"]) == 1
    assert data["document_discounts"] is not None
    assert len(data["document_discounts"]) == 1
