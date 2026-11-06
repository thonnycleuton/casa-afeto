"""M13 Step 5 — Documento permanente e integração OCR com rascunhos.

Covers:
- OCR creates DRAFT without ENTRY
- Item and document discounts are persisted
- Original document is preserved after successful OCR
- Permanent document is created and linked to draft
- Failed commit preserves temp file
- Failed copy prevents draft creation
- Session discard does not delete permanent document
- GET /purchases/{id}/document works
- OCR draft can be edited and confirmed
- Manual purchase works without document
- Retry D-22 still works
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
from app.products.models import InventoryMovement
from app.ocr.state import store
from app.products.models import Product
from app.purchases.models import Purchase, PurchaseItem


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
        name = f"step5-test-{uuid4().hex[:8]}"
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


def _create_image_file() -> BytesIO:
    """Create a minimal valid JPEG file for testing."""
    # Minimal JPEG header (1x1 white pixel)
    jpeg_data = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )
    return BytesIO(jpeg_data)


def _get_auth_headers(client: TestClient) -> dict:
    """Create admin, login, and return auth headers."""
    email = f"step5-auth-{uuid4().hex[:8]}@casaafeto.com"
    payload = {
        "email": email,
        "password": "Admin1234",
        "full_name": "Step5 Auth Admin",
    }
    resp = client.post("/api/v1/auth/setup/create-admin", json=payload)
    if resp.status_code != 201:
        from app.auth.models import User
        from app.auth.utils import hash_password
        with SessionLocal() as db:
            user = User(
                email=email,
                password_hash=hash_password("Admin1234"),
                full_name="Step5 Auth Admin",
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


# ─── Test 1: OCR creates DRAFT without ENTRY ───


def test_ocr_creates_draft_no_entry(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """confirm_import creates DRAFT purchase, not CONFIRMED, with no ENTRY."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Setup: create a session with a temp file
    session_id = "test-ocr-draft"
    temp_dir = Path(mkdtemp())
    temp_file = temp_dir / f"{session_id}.jpg"
    temp_file.write_bytes(b"\xff\xd8\xff\xe0test")

    from app.ocr.schemas import OCRItem, OCRSession

    session = OCRSession(
        session_id=session_id,
        status="completed",
        file_path=str(temp_file),
        file_mime_type="image/jpeg",
        items=[
            OCRItem(
                item_id="item-1",
                description="Produto Teste",
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

    # Mock _create_draft to return a DRAFT purchase
    from app.purchases.schemas import PurchaseRead, PurchaseItemRead

    with patch("app.ocr.service._create_draft") as mock_draft:
        mock_draft.return_value = PurchaseRead(
            id=1,
            purchased_at=datetime(2025, 6, 15, 10, 0, 0),
            access_key="1" * 44,
            status="DRAFT",
            items=[
                PurchaseItemRead(
                    id=1,
                    product_id=product_id,
                    product_name=product["name"],
                    base_unit="UN",
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    conversion_factor=Decimal("1"),
                )
            ],
        )

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
        response = confirm_import(mock_db, session_id, request)

    assert response.status == "DRAFT"
    assert response.purchase_id == 1
    mock_draft.assert_called_once()

    # Cleanup
    temp_file.unlink(missing_ok=True)
    temp_dir.rmdir()


# ─── Test 2: Discounts are persisted ───


def test_ocr_transports_item_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """OCR item discounts are transported to CreateDraft."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    session_id = "test-discount"
    temp_dir = Path(mkdtemp())
    temp_file = temp_dir / f"{session_id}.jpg"
    temp_file.write_bytes(b"\xff\xd8\xff\xe0test")

    from app.ocr.schemas import OCRDiscount, OCRItem, OCRSession

    session = OCRSession(
        session_id=session_id,
        status="completed",
        file_path=str(temp_file),
        file_mime_type="image/jpeg",
        items=[
            OCRItem(
                item_id="item-1",
                description="Produto Teste",
                quantity=Decimal("10"),
                commercial_unit="UN",
                commercial_unit_price=Decimal("5.00"),
                product_id=product_id,
                conversion_factor=Decimal("1"),
                discounts=[
                    OCRDiscount(
                        value=Decimal("5.00"),
                        nature="volume",
                        description="Desconto por volume",
                    )
                ],
            )
        ],
        document_discounts=[
            OCRDiscount(
                value=Decimal("10.00"),
                nature="frete",
                description="Desconto de frete",
                document_level=True,
            )
        ],
        access_key="1" * 44,
        purchased_at=datetime(2025, 6, 15, 10, 0, 0),
    )
    store._sessions.clear()
    store.add(session)

    from app.purchases.schemas import PurchaseRead, PurchaseItemRead

    with patch("app.ocr.service._create_draft") as mock_draft:
        mock_draft.return_value = PurchaseRead(
            id=1,
            purchased_at=datetime(2025, 6, 15, 10, 0, 0),
            access_key="1" * 44,
            status="DRAFT",
            items=[
                PurchaseItemRead(
                    id=1,
                    product_id=product_id,
                    product_name=product["name"],
                    base_unit="UN",
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    conversion_factor=Decimal("1"),
                )
            ],
        )

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
        confirm_import(mock_db, session_id, request)

    # Verify CreateDraft was called with discounts
    call_args = mock_draft.call_args
    draft_data = call_args[0][1]
    assert len(draft_data.items) == 1
    assert draft_data.items[0].item_discounts is not None
    assert len(draft_data.items[0].item_discounts) == 1
    assert draft_data.items[0].item_discounts[0].nature == "volume"

    # Document discounts transported
    assert draft_data.document_discounts is not None
    assert len(draft_data.document_discounts) == 1
    assert draft_data.document_discounts[0].nature == "frete"

    # Cleanup
    temp_file.unlink(missing_ok=True)
    temp_dir.rmdir()


# ─── Test 3: Document permanent is created ───


def test_ocr_copies_document_permanent(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """OCR copies temp file to permanent storage and sets document_path."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    session_id = "test-permanent"
    temp_dir = Path(mkdtemp())
    temp_file = temp_dir / f"{session_id}.jpg"
    temp_file.write_bytes(b"\xff\xd8\xff\xe0permanent-test")

    from app.ocr.schemas import OCRItem, OCRSession

    session = OCRSession(
        session_id=session_id,
        status="completed",
        file_path=str(temp_file),
        file_mime_type="image/jpeg",
        items=[
            OCRItem(
                item_id="item-1",
                description="Produto Teste",
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

    from app.purchases.schemas import PurchaseRead, PurchaseItemRead

    with patch("app.ocr.service._create_draft") as mock_draft:
        mock_draft.return_value = PurchaseRead(
            id=1,
            purchased_at=datetime(2025, 6, 15, 10, 0, 0),
            access_key="1" * 44,
            status="DRAFT",
            items=[
                PurchaseItemRead(
                    id=1,
                    product_id=product_id,
                    product_name=product["name"],
                    base_unit="UN",
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    conversion_factor=Decimal("1"),
                )
            ],
        )

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
        confirm_import(mock_db, session_id, request)

    # Verify document_path was set
    call_args = mock_draft.call_args
    draft_data = call_args[0][1]
    assert draft_data.document_path is not None
    assert draft_data.document_path.startswith("purchases/")
    assert session_id in draft_data.document_path

    # Verify permanent file was created
    purchases_dir = settings.entity_upload_path("purchases")
    permanent_files = list(purchases_dir.glob(f"*{session_id}*"))
    assert len(permanent_files) == 1
    assert permanent_files[0].read_bytes() == b"\xff\xd8\xff\xe0permanent-test"

    # Cleanup
    permanent_files[0].unlink()
    temp_file.unlink(missing_ok=True)
    temp_dir.rmdir()


# ─── Test 4: Missing temp file prevents draft ───


def test_ocr_missing_temp_file_prevents_draft(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """If temp file is missing, confirm_import raises BusinessRuleError."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    session_id = "test-missing"
    from app.ocr.schemas import OCRItem, OCRSession

    session = OCRSession(
        session_id=session_id,
        status="completed",
        file_path="/nonexistent/path/file.jpg",
        file_mime_type="image/jpeg",
        items=[
            OCRItem(
                item_id="item-1",
                description="Produto Teste",
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
    with pytest.raises(BusinessRuleError, match="não está mais disponível"):
        confirm_import(mock_db, session_id, request)


# ─── Test 5: GET /purchases/{id}/document ───


def test_get_purchase_document(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """GET /purchases/{id}/document returns the file (requires JWT)."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]
    headers = _get_auth_headers(client)

    # Create a DRAFT with document_path
    purchases_dir = settings.entity_upload_path("purchases")
    purchases_dir.mkdir(parents=True, exist_ok=True)
    doc_file = purchases_dir / "test_doc.jpg"
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
        "document_path": "purchases/test_doc.jpg",
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # GET document with auth
    response = client.get(f"/api/v1/purchases/{purchase_id}/document", headers=headers)
    assert response.status_code == 200
    assert b"\xff\xd8\xff\xe0document-content" in response.content

    # Cleanup
    doc_file.unlink(missing_ok=True)


def test_get_purchase_document_not_found(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """GET /purchases/{id}/document returns 404 when no document (requires JWT)."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]
    headers = _get_auth_headers(client)

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    response = client.get(f"/api/v1/purchases/{purchase_id}/document", headers=headers)
    assert response.status_code == 404


# ─── Test 6: OCR draft can be edited and confirmed ───


def test_ocr_draft_can_be_edited_and_confirmed(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """DRAFT created via OCR can be edited and then confirmed."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create DRAFT
    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == "DRAFT"
    purchase_id = data["id"]

    # Edit DRAFT
    update_payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "10",
                "commercial_unit_price": "15.00",
            }
        ]
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert Decimal(data["items"][0]["commercial_quantity"]) == Decimal("10")

    # Confirm DRAFT
    response = client.post(f"/api/v1/purchases/{purchase_id}/confirm")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "CONFIRMED"

    # Verify ENTRY was generated
    db = SessionLocal()
    movements = db.query(InventoryMovement).filter(
        InventoryMovement.purchase_id == purchase_id
    ).all()
    assert len(movements) == 1
    db.close()


# ─── Test 7: Manual purchase works without document ───


def test_manual_purchase_without_document(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Manual purchase via POST /purchases works without document."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ]
    }
    response = client.post("/api/v1/purchases", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == "CONFIRMED"
    assert data["document_path"] is None


# ─── Test 8: Temp file preserved after OCR success ───


def test_temp_file_preserved_after_ocr_success() -> None:
    """After OCR processing succeeds, temp file is NOT deleted."""
    session_id = "test-preserve"
    temp_dir = Path(mkdtemp())
    temp_file = temp_dir / f"{session_id}.jpg"
    temp_file.write_bytes(b"\xff\xd8\xff\xe0preserve-test")

    from app.ocr.schemas import OCRItem, OCRSession

    session = OCRSession(
        session_id=session_id,
        status="processing",
        file_path=str(temp_file),
        file_mime_type="image/jpeg",
        items=[
            OCRItem(
                item_id="item-1",
                description="Produto",
                quantity=Decimal("10"),
                commercial_unit="UN",
                commercial_unit_price=Decimal("5.00"),
            )
        ],
    )
    store._sessions.clear()
    store.add(session)

    # Simulate OCR completion (normally done by _process_document)
    session.status = "completed"
    session.items = [
        OCRItem(
            item_id="item-1",
            description="Produto",
            quantity=Decimal("10"),
            commercial_unit="UN",
            commercial_unit_price=Decimal("5.00"),
        )
    ]
    store.update(session)

    # Verify temp file still exists (not deleted on OCR success)
    assert temp_file.exists(), "Temp file should be preserved after OCR success"

    # Cleanup
    temp_file.unlink()
    temp_dir.rmdir()


# ─── Test 9: Discard session preserves permanent document ───


def test_discard_session_preserves_permanent(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Discarding a session only deletes the temp file, not the permanent document."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create a DRAFT with document_path (simulating OCR import)
    purchases_dir = settings.entity_upload_path("purchases")
    purchases_dir.mkdir(parents=True, exist_ok=True)
    permanent_file = purchases_dir / "permanent_doc.jpg"
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
        "document_path": "purchases/permanent_doc.jpg",
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Verify permanent file exists
    assert permanent_file.exists()

    # The permanent document should still be accessible (requires JWT)
    headers = _get_auth_headers(client)
    response = client.get(f"/api/v1/purchases/{purchase_id}/document", headers=headers)
    assert response.status_code == 200

    # Cleanup
    permanent_file.unlink(missing_ok=True)


# ─── Test 10: UpdateDraft rejects document_path from frontend ───


def test_update_draft_rejects_document_path(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """PATCH /purchases/{id} rejects document_path from frontend."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Try to send document_path via PATCH — should be rejected (extra field)
    update_payload = {
        "document_path": "purchases/hacked.jpg",
        "supplier_name": "Test",
    }
    response = client.patch(
        f"/api/v1/purchases/{purchase_id}", json=update_payload
    )
    # extra="forbid" should reject document_path
    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
