"""M13 Fase 1 — OCR Infrastructure Tests.

Covers:
- Upload validation (file type, size)
- Session creation with UUID
- Background processing (mocked Gemini)
- Status polling
- Session not found (404)
- Authentication (401)
- File deletion after processing
- Orphan file cleanup on startup
- Gemini failure handling
- Matching functions
- Gemini response parsing
"""

from __future__ import annotations

import io
import json
import os
import sys
import time
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.ocr.gemini_client import call_gemini_ocr, parse_gemini_response
from app.ocr.matching import exact_match, fuzzy_match, normalize_name, substring_match
from app.ocr.schemas import OCRItem, OCRSession
from app.ocr.state import cleanup_orphan_files, store


# ─── Helpers ───

def _create_jpeg() -> bytes:
    """Create a minimal valid JPEG image (1x1 red pixel)."""
    # Minimal JPEG binary data — valid SOI + APP0 + DQT + SOF + DHT + SOS + EOI
    return (
        b"\xff\xd8"
        b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07"
        b"\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14"
        b"\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c$\x2e\x27\x2e\x1c\x1c(\x0e"
        b"\x1c\x1c\x2b\x3e\x3e\x3e\x36\x2f\x3b\x3e\x3e\x3e\x3e\x3e\x3e"
        b"\x3e\x3e\x3e\x3e\x3e\x3e\x3e\x3e\x3e\x3e\x3e\x3e\x3e\x3e\x3e"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06"
        b"\x07\x08\x09\x0a\x0b"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5\xd0"
        b"\xff\xd9"
    )


def _create_png() -> bytes:
    """Create a minimal valid PNG image."""
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f"
        b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def _mock_gemini_response() -> str:
    """Return a mock Gemini JSON response."""
    return json.dumps({
        "document_total": 150.00,
        "purchased_at": "2024-01-15",
        "access_key": "1234567890123456789012345678901234567890",
        "items": [
            {
                "description": "Arroz Tipo 1 5kg",
                "quantity": 10,
                "commercial_unit": "saco",
                "commercial_unit_price": 25.00,
                "subtotal_printed": 250.00,
                "subtotal_calculated": 250.00,
                "discounts": [],
            },
            {
                "description": "Feijao Carioca 1kg",
                "quantity": 20,
                "commercial_unit": "pacote",
                "commercial_unit_price": 8.50,
                "subtotal_printed": 170.00,
                "subtotal_calculated": 170.00,
                "discounts": [
                    {
                        "value": 10.00,
                        "nature": "item",
                        "description": "Desconto promocional",
                    }
                ],
            },
        ],
        "document_discounts": [
            {
                "value": 5.00,
                "nature": "documento",
                "description": "Desconto por pagamento a vista",
            }
        ],
    })


def _get_auth_headers(client: TestClient) -> dict:
    """Create admin via setup endpoint, login, and return auth headers."""
    email = f"ocr-admin-{uuid4().hex[:8]}@casaafeto.com"
    payload = {
        "email": email,
        "password": "Admin1234",
        "full_name": "OCR Test Admin",
    }
    resp = client.post("/api/v1/auth/setup/create-admin", json=payload)
    if resp.status_code != 201:
        # Admin may already exist — try creating a regular user instead
        from app.core.database import SessionLocal
        from app.auth.models import User
        from app.auth.utils import hash_password
        with SessionLocal() as db:
            user = User(
                email=email,
                password_hash=hash_password("Admin1234"),
                full_name="OCR Test Admin",
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


# ─── Upload validation tests ───

class TestUploadValidation:
    """Test file type and size validation on upload."""

    def test_upload_valid_jpeg(self, client: TestClient) -> None:
        """Valid JPEG upload creates session and returns 201."""
        headers = _get_auth_headers(client)
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        with patch("app.ocr.service.call_gemini_ocr"):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )

        assert resp.status_code == 201
        data = resp.json()
        assert "session_id" in data
        assert data["status"] in ("pending", "processing")

    def test_upload_valid_png(self, client: TestClient) -> None:
        """Valid PNG upload creates session."""
        headers = _get_auth_headers(client)
        files = {"file": ("document.png", io.BytesIO(_create_png()), "image/png")}

        with patch("app.ocr.service.call_gemini_ocr"):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )

        assert resp.status_code == 201

    def test_upload_invalid_type(self, client: TestClient) -> None:
        """Upload of unsupported file type returns 400."""
        headers = _get_auth_headers(client)
        files = {"file": ("document.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}

        resp = client.post(
            "/api/v1/ocr/upload",
            files=files,
            headers=headers,
        )

        assert resp.status_code == 400
        assert "não suportado" in resp.json()["detail"].lower()

    def test_upload_empty_file(self, client: TestClient) -> None:
        """Upload of empty file returns 400."""
        headers = _get_auth_headers(client)
        files = {"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}

        resp = client.post(
            "/api/v1/ocr/upload",
            files=files,
            headers=headers,
        )

        assert resp.status_code == 400

    def test_upload_without_auth(self, client: TestClient) -> None:
        """Upload without JWT token returns 401 or 403."""
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        with patch("app.ocr.service.call_gemini_ocr"):
            resp = client.post("/api/v1/ocr/upload", files=files)

        # HTTPBearer returns 403 when no token; 401 when token is invalid
        assert resp.status_code in (401, 403)

    def test_upload_with_invalid_token(self, client: TestClient) -> None:
        """Upload with invalid JWT token returns 401."""
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        with patch("app.ocr.service.call_gemini_ocr"):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers={"Authorization": "Bearer invalid.token.here"},
            )

        assert resp.status_code == 401


# ─── Session & polling tests ───

class TestSessionAndPolling:

    def test_session_id_is_uuid(self, client: TestClient) -> None:
        """Session ID is a valid UUID hex string."""
        headers = _get_auth_headers(client)
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        with patch("app.ocr.service.call_gemini_ocr"):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )

        assert resp.status_code == 201
        session_id = resp.json()["session_id"]
        # UUID hex is 32 chars
        assert len(session_id) == 32

    def test_poll_status_pending(self, client: TestClient) -> None:
        """Polling returns current session status."""
        headers = _get_auth_headers(client)
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        # Mock with empty result so background task completes cleanly
        mock_result = MagicMock()
        mock_result.document_total = None
        mock_result.purchased_at = None
        mock_result.access_key = None
        mock_result.items = []
        mock_result.document_discounts = []

        with patch("app.ocr.service.call_gemini_ocr", return_value=mock_result):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )

        session_id = resp.json()["session_id"]

        # Wait for background task to complete
        time.sleep(0.5)

        resp = client.get(
            f"/api/v1/ocr/{session_id}/status",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == session_id
        assert data["status"] == "completed"

    def test_poll_nonexistent_session(self, client: TestClient) -> None:
        """Polling nonexistent session returns 404."""
        headers = _get_auth_headers(client)

        resp = client.get(
            f"/api/v1/ocr/{uuid4().hex}/status",
            headers=headers,
        )

        assert resp.status_code == 404

    def test_poll_without_auth(self, client: TestClient) -> None:
        """Polling without JWT returns 401 or 403."""
        resp = client.get(f"/api/v1/ocr/{uuid4().hex}/status")
        assert resp.status_code in (401, 403)

    def test_session_stores_mime_type(self, client: TestClient) -> None:
        """Session stores the MIME type of the uploaded file."""
        headers = _get_auth_headers(client)

        # Test PNG upload stores image/png
        files = {"file": ("document.png", io.BytesIO(_create_png()), "image/png")}
        with patch("app.ocr.service.call_gemini_ocr"):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )
        assert resp.status_code == 201
        session_id = resp.json()["session_id"]
        session = store.get(session_id)
        assert session is not None
        assert session.file_mime_type == "image/png"
        store.remove(session_id)

        # Test JPEG upload stores image/jpeg
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}
        with patch("app.ocr.service.call_gemini_ocr"):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )
        assert resp.status_code == 201
        session_id = resp.json()["session_id"]
        session = store.get(session_id)
        assert session is not None
        assert session.file_mime_type == "image/jpeg"
        store.remove(session_id)


# ─── Background processing tests (mocked Gemini) ───

class TestBackgroundProcessing:

    def test_processing_completes_successfully(self, client: TestClient) -> None:
        """Successful Gemini call updates session to completed."""
        headers = _get_auth_headers(client)
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        mock_result = MagicMock()
        mock_result.document_total = Decimal("150.00")
        mock_result.purchased_at = None
        mock_result.access_key = "TEST-ACCESS-KEY"
        mock_result.items = [
            OCRItem(
                item_id="item-1",
                description="Arroz Tipo 1",
                quantity=Decimal("10"),
                commercial_unit="saco",
                commercial_unit_price=Decimal("25.00"),
            )
        ]
        mock_result.document_discounts = []

        with patch("app.ocr.service.call_gemini_ocr", return_value=mock_result):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )

        session_id = resp.json()["session_id"]

        # Wait for background task to complete
        time.sleep(0.5)

        resp = client.get(
            f"/api/v1/ocr/{session_id}/status",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert Decimal(str(data["document_total"])) == Decimal("150.00")
        assert data["access_key"] == "TEST-ACCESS-KEY"
        assert len(data["items"]) == 1
        assert data["items"][0]["description"] == "Arroz Tipo 1"

    def test_processing_failure_marks_session_failed(self, client: TestClient) -> None:
        """Gemini failure marks session as failed with error message."""
        headers = _get_auth_headers(client)
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        with patch(
            "app.ocr.service.call_gemini_ocr",
            side_effect=RuntimeError("API key inválida"),
        ):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )

        session_id = resp.json()["session_id"]
        time.sleep(0.5)

        resp = client.get(
            f"/api/v1/ocr/{session_id}/status",
            headers=headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert data["error"] is not None
        assert "API key" in data["error"] or "inválida" in data["error"]

    def test_file_preserved_after_ocr_processing(self, client: TestClient) -> None:
        """Temporary file is preserved after OCR processing completes (Step 5).

        The file is kept until confirm_import copies it to permanent storage.
        This allows the operator to review and confirm without time pressure.
        """
        headers = _get_auth_headers(client)
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        mock_result = MagicMock()
        mock_result.document_total = None
        mock_result.purchased_at = None
        mock_result.access_key = None
        mock_result.items = []
        mock_result.document_discounts = []

        with patch("app.ocr.service.call_gemini_ocr", return_value=mock_result):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )

        session_id = resp.json()["session_id"]
        time.sleep(0.5)

        # Check that session is completed
        resp = client.get(
            f"/api/v1/ocr/{session_id}/status",
            headers=headers,
        )
        assert resp.status_code == 200

        # Verify file is PRESERVED after OCR processing (Step 5 change)
        session = store.get(session_id)
        assert session is not None
        assert session.status == "completed"
        assert session.file_path is not None
        assert Path(session.file_path).exists()

    def test_file_preserved_on_failure(self, client: TestClient) -> None:
        """Temporary file is preserved when processing fails so it can be retried (M13)."""
        headers = _get_auth_headers(client)
        files = {"file": ("document.jpg", io.BytesIO(_create_jpeg()), "image/jpeg")}

        with patch(
            "app.ocr.service.call_gemini_ocr",
            side_effect=RuntimeError("Simulated failure"),
        ):
            resp = client.post(
                "/api/v1/ocr/upload",
                files=files,
                headers=headers,
            )

        session_id = resp.json()["session_id"]
        time.sleep(0.5)

        session = store.get(session_id)
        assert session is not None
        assert session.status == "failed"
        # File must be preserved on failure for retry
        assert session.file_path is not None
        assert Path(session.file_path).exists()

    def test_create_task_failure_cleanup(self) -> None:
        """If asyncio.create_task fails during upload, session and file are cleaned up (M13)."""
        import app.ocr.service as service_mod
        from fastapi import UploadFile

        # Record state before the call
        before_session_count = len(store._sessions)
        upload_dir = settings.entity_upload_path("ocr")
        before_files = set(f.name for f in upload_dir.iterdir()) if upload_dir.exists() else set()

        # Track whether close() was called on the coroutine
        close_called = [False]

        class CoroutineWrapper:
            """Wrapper that tracks close() calls and delegates to the real coroutine."""
            def __init__(self, coro):
                self._coro = coro
            def close(self):
                close_called[0] = True
                self._coro.close()

        original_process = service_mod._process_document

        def wrapped_process(session_id):
            real_coro = original_process(session_id)
            return CoroutineWrapper(real_coro)

        def failing_create_task(coro, *args, **kwargs):
            raise RuntimeError("Task scheduler unavailable")

        upload_file = UploadFile(
            file=io.BytesIO(_create_jpeg()),
            filename="document.jpg",
            headers={"content-type": "image/jpeg"},
        )

        with patch("app.ocr.service._process_document", wrapped_process):
            with patch("app.ocr.service.asyncio.create_task", side_effect=failing_create_task):
                with pytest.raises(RuntimeError, match="Task scheduler unavailable"):
                    service_mod.upload_document(upload_file)

        # Verify the coroutine wrapper's close() was called by production code
        assert close_called[0], (
            "Coroutine.close() was not called by production code"
        )

        # Verify no session was leaked
        after_session_count = len(store._sessions)
        assert after_session_count == before_session_count, (
            f"Session leak detected: {before_session_count} before, {after_session_count} after"
        )

        # Verify no new temp file was left behind
        after_files = set(f.name for f in upload_dir.iterdir()) if upload_dir.exists() else set()
        new_files = after_files - before_files
        assert not new_files, f"Orphan temp file(s) left behind: {new_files}"


# ─── Orphan cleanup tests ───

class TestOrphanCleanup:

    def test_cleanup_removes_old_files(self, tmp_path: Path) -> None:
        """Old files (> 1 hour) are removed on cleanup."""
        # Create a file with old mtime
        old_file = tmp_path / "old_session.jpg"
        old_file.write_bytes(b"fake image data")
        # Set mtime to 2 hours ago
        old_time = time.time() - 7200
        os.utime(old_file, (old_time, old_time))

        removed = cleanup_orphan_files(tmp_path, max_age_seconds=3600)

        assert removed == 1
        assert not old_file.exists()

    def test_cleanup_keeps_recent_files(self, tmp_path: Path) -> None:
        """Recent files are not removed."""
        recent_file = tmp_path / "recent_session.jpg"
        recent_file.write_bytes(b"fake image data")

        removed = cleanup_orphan_files(tmp_path, max_age_seconds=3600)

        assert removed == 0
        assert recent_file.exists()

    def test_cleanup_nonexistent_dir(self, tmp_path: Path) -> None:
        """Cleanup on nonexistent directory returns 0."""
        nonexistent = tmp_path / "nonexistent"
        removed = cleanup_orphan_files(nonexistent)
        assert removed == 0


# ─── Gemini response parsing tests ───

class TestGeminiParsing:

    def test_parse_valid_response(self) -> None:
        """Valid JSON response is parsed correctly."""
        text = _mock_gemini_response()
        result = parse_gemini_response(text)

        assert result.document_total == Decimal("150.00")
        assert result.access_key == "1234567890123456789012345678901234567890"
        assert len(result.items) == 2
        assert result.items[0].description == "Arroz Tipo 1 5kg"
        assert result.items[0].quantity == Decimal("10")
        assert result.items[0].commercial_unit_price == Decimal("25.00")
        assert result.items[0].subtotal_printed == Decimal("250.00")
        assert result.items[0].subtotal_calculated == Decimal("250.00")
        # Discounts
        assert len(result.items[1].discounts) == 1
        assert result.items[1].discounts[0].value == Decimal("10.00")
        assert result.items[1].discounts[0].item_id is not None
        assert result.items[1].discounts[0].document_level is False
        # Document discounts
        assert len(result.document_discounts) == 1
        assert result.document_discounts[0].document_level is True

    def test_parse_response_with_markdown_fences(self) -> None:
        """Response wrapped in markdown code fences is parsed correctly."""
        text = f"```json\n{_mock_gemini_response()}\n```"
        result = parse_gemini_response(text)

        assert result.document_total == Decimal("150.00")
        assert len(result.items) == 2

    def test_parse_response_with_missing_fields(self) -> None:
        """Response with missing fields preserves None values (D-3)."""
        text = json.dumps({
            "document_total": None,
            "purchased_at": None,
            "access_key": None,
            "items": [
                {
                    "description": "Produto sem preço",
                    "quantity": 5,
                    "commercial_unit": None,
                    "commercial_unit_price": None,
                    "subtotal_printed": None,
                    "subtotal_calculated": None,
                    "discounts": [],
                }
            ],
            "document_discounts": [],
        })
        result = parse_gemini_response(text)

        assert result.document_total is None
        assert result.access_key is None
        assert result.items[0].commercial_unit_price is None
        assert result.items[0].subtotal_printed is None

    def test_parse_invalid_json(self) -> None:
        """Invalid JSON raises ValueError."""
        with pytest.raises(ValueError, match="não é JSON válido"):
            parse_gemini_response("não é JSON")

    def test_parse_empty_items(self) -> None:
        """Response with no items returns empty list."""
        text = json.dumps({
            "document_total": 0,
            "purchased_at": None,
            "access_key": None,
            "items": [],
            "document_discounts": [],
        })
        result = parse_gemini_response(text)

        assert result.items == []

    def test_item_ids_are_unique(self) -> None:
        """Each item gets a unique stable item_id."""
        text = _mock_gemini_response()
        result = parse_gemini_response(text)

        ids = [item.item_id for item in result.items]
        assert len(ids) == len(set(ids))  # All unique
        assert all(len(item_id) == 32 for item_id in ids)  # UUID hex format

    def test_call_gemini_ocr_uses_correct_mime_type(self, tmp_path: Path) -> None:
        """call_gemini_ocr passes the actual MIME type to Gemini, not hardcoded image/jpeg."""
        image_file = tmp_path / "test.png"
        image_file.write_bytes(_create_png())

        mock_response = MagicMock()
        mock_response.text = _mock_gemini_response()

        mock_types = MagicMock()
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        mock_genai_module = MagicMock()
        mock_genai_module.Client.return_value = mock_client
        mock_genai_module.types = mock_types

        mock_google = MagicMock()
        mock_google.genai = mock_genai_module

        saved_modules = {}
        for key in list(sys.modules.keys()):
            if key.startswith("google"):
                saved_modules[key] = sys.modules.pop(key)

        sys.modules["google"] = mock_google
        sys.modules["google.genai"] = mock_genai_module

        try:
            with patch.object(settings, "GEMINI_API_KEY", "test-key"):
                with patch("app.ocr.gemini_client.parse_gemini_response", return_value=MagicMock()):
                    call_gemini_ocr(image_file, mime_type="image/png")
        finally:
            for key in ("google", "google.genai"):
                sys.modules.pop(key, None)
            sys.modules.update(saved_modules)

        # Check that Part.from_bytes was called with the correct mime_type
        from_bytes_call = mock_types.Part.from_bytes.call_args
        assert from_bytes_call is not None
        assert from_bytes_call.kwargs.get("mime_type") == "image/png", (
            f"Expected mime_type 'image/png', got '{from_bytes_call.kwargs.get('mime_type')}'"
        )

    def test_call_gemini_ocr_defaults_to_jpeg(self, tmp_path: Path) -> None:
        """call_gemini_ocr defaults to image/jpeg when mime_type is None."""
        image_file = tmp_path / "test.jpg"
        image_file.write_bytes(_create_jpeg())

        mock_response = MagicMock()
        mock_response.text = _mock_gemini_response()

        mock_types = MagicMock()
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        mock_genai_module = MagicMock()
        mock_genai_module.Client.return_value = mock_client
        mock_genai_module.types = mock_types

        mock_google = MagicMock()
        mock_google.genai = mock_genai_module

        saved_modules = {}
        for key in list(sys.modules.keys()):
            if key.startswith("google"):
                saved_modules[key] = sys.modules.pop(key)

        sys.modules["google"] = mock_google
        sys.modules["google.genai"] = mock_genai_module

        try:
            with patch.object(settings, "GEMINI_API_KEY", "test-key"):
                with patch("app.ocr.gemini_client.parse_gemini_response", return_value=MagicMock()):
                    call_gemini_ocr(image_file, mime_type=None)
        finally:
            for key in ("google", "google.genai"):
                sys.modules.pop(key, None)
            sys.modules.update(saved_modules)

        # Check that Part.from_bytes was called with the default mime_type
        from_bytes_call = mock_types.Part.from_bytes.call_args
        assert from_bytes_call is not None
        assert from_bytes_call.kwargs.get("mime_type") == "image/jpeg"


# ─── Matching tests ───

class TestMatching:

    def test_normalize_name_removes_accents(self) -> None:
        """Normalization removes accents and lowercases."""
        assert normalize_name("Café com Açúcar") == "cafe com acucar"
        assert normalize_name("  Feijão  ") == "feijao"

    def test_normalize_name_collapse_whitespace(self) -> None:
        """Normalization collapses multiple spaces."""
        assert normalize_name("Arroz   Tipo   1") == "arroz tipo 1"

    def test_levenshtein_based_fuzzy(self) -> None:
        """Fuzzy matching finds similar names."""
        from app.ocr.matching import _levenshtein_distance

        assert _levenshtein_distance("arroz", "arroz") == 0
        assert _levenshtein_distance("arroz", "arroz ") == 1
        assert _levenshtein_distance("", "") == 0

    def test_match_suggestion_includes_conversion_factor(self) -> None:
        """MatchSuggestion.to_dict() includes commercial_conversion_factor and base_unit."""
        from decimal import Decimal

        from app.ocr.matching import MatchSuggestion
        from app.products.models import Product

        product = Product(
            id=1,
            name="Arroz 5kg",
            base_unit="KG",
            commercial_conversion_factor=Decimal("12"),
        )
        suggestion = MatchSuggestion(product, "exact", 1.0)
        d = suggestion.to_dict()

        assert d["product_id"] == 1
        assert d["product_name"] == "Arroz 5kg"
        assert d["base_unit"] == "KG"
        assert d["commercial_conversion_factor"] == "12"

    def test_match_suggestion_with_null_conversion_factor(self) -> None:
        """MatchSuggestion handles None commercial_conversion_factor."""
        from app.ocr.matching import MatchSuggestion
        from app.products.models import Product

        product = Product(
            id=2,
            name="Feijao 1kg",
            base_unit="KG",
            commercial_conversion_factor=None,
        )
        suggestion = MatchSuggestion(product, "fuzzy", 0.8)
        d = suggestion.to_dict()

        assert d["base_unit"] == "KG"
        assert d["commercial_conversion_factor"] is None


# ─── Store tests ───

class TestStore:

    def test_add_and_get(self) -> None:
        """Session can be added and retrieved."""
        session = OCRSession(
            session_id="test-123",
            status="pending",
        )
        store.add(session)

        retrieved = store.get("test-123")
        assert retrieved is not None
        assert retrieved.session_id == "test-123"

        store.remove("test-123")

    def test_get_nonexistent(self) -> None:
        """Getting nonexistent session returns None."""
        assert store.get("nonexistent") is None

    def test_update(self) -> None:
        """Session can be updated."""
        session = OCRSession(
            session_id="test-update",
            status="pending",
        )
        store.add(session)

        session.status = "completed"
        store.update(session)

        retrieved = store.get("test-update")
        assert retrieved is not None
        assert retrieved.status == "completed"

        store.remove("test-update")

    def test_remove(self) -> None:
        """Session can be removed."""
        session = OCRSession(
            session_id="test-remove",
            status="pending",
        )
        store.add(session)
        store.remove("test-remove")

        assert store.get("test-remove") is None

    def test_try_claim_reprocess_success(self) -> None:
        """try_claim_reprocess transitions failed -> pending and returns the session."""
        session = OCRSession(
            session_id="reprocess-success",
            status="failed",
        )
        store.add(session)

        claimed = store.try_claim_reprocess("reprocess-success")

        assert claimed is not None
        assert claimed.session_id == "reprocess-success"
        assert claimed.status == "pending"

        # Verify the stored session is also updated
        retrieved = store.get("reprocess-success")
        assert retrieved is not None
        assert retrieved.status == "pending"

        store.remove("reprocess-success")

    def test_try_claim_reprocess_nonexistent(self) -> None:
        """try_claim_reprocess returns None for nonexistent session."""
        result = store.try_claim_reprocess("does-not-exist")
        assert result is None

    def test_try_claim_reprocess_wrong_status(self) -> None:
        """try_claim_reprocess returns None when session is not in 'failed' status."""
        session = OCRSession(
            session_id="reprocess-wrong-status",
            status="completed",
        )
        store.add(session)

        result = store.try_claim_reprocess("reprocess-wrong-status")
        assert result is None

        # Status should remain unchanged
        retrieved = store.get("reprocess-wrong-status")
        assert retrieved is not None
        assert retrieved.status == "completed"

        store.remove("reprocess-wrong-status")

    def test_try_claim_reprocess_concurrent(self) -> None:
        """Only one concurrent call can claim the same failed session."""
        import threading

        session = OCRSession(
            session_id="reprocess-concurrent",
            status="failed",
        )
        store.add(session)

        results = []

        def claim():
            result = store.try_claim_reprocess("reprocess-concurrent")
            results.append(result)

        t1 = threading.Thread(target=claim)
        t2 = threading.Thread(target=claim)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exactly one thread should have successfully claimed the session
        claimed = [r for r in results if r is not None]
        none_results = [r for r in results if r is None]

        assert len(claimed) == 1, (
            f"Expected exactly 1 claim, got {len(claimed)}"
        )
        assert len(none_results) == 1, (
            f"Expected exactly 1 None, got {len(none_results)}"
        )
        assert claimed[0].session_id == "reprocess-concurrent"
        assert claimed[0].status == "pending"

        store.remove("reprocess-concurrent")


# ─── Reprocess service tests ───

class TestReprocessService:
    """Test reprocess_document() service function."""

    def test_reprocess_nonexistent_session(self) -> None:
        """reprocess_document raises ValueError for nonexistent session."""
        from app.ocr.service import reprocess_document

        with pytest.raises(ValueError, match="não encontrada"):
            reprocess_document("does-not-exist")

    def test_reprocess_wrong_status(self) -> None:
        """reprocess_document raises ValueError when session is not failed."""
        from app.ocr.service import reprocess_document

        session = OCRSession(
            session_id="reprocess-wrong-status",
            status="completed",
        )
        store.add(session)

        with pytest.raises(ValueError, match="não 'failed'"):
            reprocess_document("reprocess-wrong-status")

        store.remove("reprocess-wrong-status")

    def test_reprocess_missing_file(self) -> None:
        """reprocess_document raises ValueError when temp file is missing."""
        from app.ocr.service import reprocess_document

        session = OCRSession(
            session_id="reprocess-missing-file",
            status="failed",
            file_path="/nonexistent/path/file.jpg",
        )
        store.add(session)

        with pytest.raises(ValueError, match="não está mais disponível"):
            reprocess_document("reprocess-missing-file")

        store.remove("reprocess-missing-file")

    def test_reprocess_missing_file_path(self) -> None:
        """reprocess_document raises ValueError when file_path is None."""
        from app.ocr.service import reprocess_document

        session = OCRSession(
            session_id="reprocess-no-file-path",
            status="failed",
            file_path=None,
        )
        store.add(session)

        with pytest.raises(ValueError, match="não está mais disponível"):
            reprocess_document("reprocess-no-file-path")

        store.remove("reprocess-no-file-path")

    def test_reprocess_success(self) -> None:
        """reprocess_document successfully claims and schedules reprocessing of a failed session."""
        from app.ocr.service import reprocess_document

        # Create a failed session with a real temp file
        upload_dir = settings.entity_upload_path("ocr")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file = upload_dir / "reprocess-success.jpg"
        temp_file.write_bytes(_create_jpeg())

        session = OCRSession(
            session_id="reprocess-success",
            status="failed",
            file_path=str(temp_file),
            file_mime_type="image/jpeg",
        )
        store.add(session)

        # Track that create_task was called (no event loop in sync test)
        task_called = [False]

        def mock_create_task(coro, *args, **kwargs):
            task_called[0] = True
            coro.close()  # Clean up the coroutine since we won't run it
            return MagicMock()

        with patch("app.ocr.service.asyncio.create_task", side_effect=mock_create_task):
            reprocess_document("reprocess-success")

        # create_task should have been called
        assert task_called[0], "asyncio.create_task was not called"

        # Session should be claimed (failed -> pending)
        session = store.get("reprocess-success")
        assert session is not None
        assert session.status == "pending"

        store.remove("reprocess-success")

    def test_reprocess_concurrent(self) -> None:
        """Only one concurrent reprocess call can claim the same failed session."""
        import threading
        import app.ocr.service as service_mod

        # Create a failed session with a real temp file
        upload_dir = settings.entity_upload_path("ocr")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file = upload_dir / "reprocess-concurrent.jpg"
        temp_file.write_bytes(_create_jpeg())

        session = OCRSession(
            session_id="reprocess-concurrent",
            status="failed",
            file_path=str(temp_file),
            file_mime_type="image/jpeg",
        )
        store.add(session)

        results = []
        errors = []

        def mock_create_task(coro, *args, **kwargs):
            coro.close()  # Clean up the coroutine since we won't run it
            return MagicMock()

        def try_reprocess():
            try:
                with patch("app.ocr.service.asyncio.create_task", side_effect=mock_create_task):
                    service_mod.reprocess_document("reprocess-concurrent")
                results.append("success")
            except ValueError as exc:
                errors.append(str(exc))

        t1 = threading.Thread(target=try_reprocess)
        t2 = threading.Thread(target=try_reprocess)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exactly one should succeed, the other should fail
        assert len(results) == 1, f"Expected 1 success, got {len(results)}"
        assert len(errors) == 1, f"Expected 1 error, got {len(errors)}"
        # The loser gets either "reivindicada" (if try_claim_reprocess returns None)
        # or "não 'failed'" (if it passes the claim check but status is already 'pending')
        error_msg = errors[0].lower()
        assert "reivindicada" in error_msg or "não 'failed'" in error_msg, (
            f"Unexpected error message: {errors[0]}"
        )

        # Clean up
        store.remove("reprocess-concurrent")
        if temp_file.exists():
            temp_file.unlink()

    def test_reprocess_task_creation_failure(self) -> None:
        """If create_task fails during reprocess, coroutine is closed and status is restored to failed."""
        import app.ocr.service as service_mod

        # Create a failed session with a real temp file
        upload_dir = settings.entity_upload_path("ocr")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file = upload_dir / "reprocess-task-fail.jpg"
        temp_file.write_bytes(_create_jpeg())

        session = OCRSession(
            session_id="reprocess-task-fail",
            status="failed",
            file_path=str(temp_file),
            file_mime_type="image/jpeg",
        )
        store.add(session)

        def failing_create_task(coro, *args, **kwargs):
            raise RuntimeError("Task scheduler unavailable")

        with patch("app.ocr.service.asyncio.create_task", side_effect=failing_create_task):
            with pytest.raises(RuntimeError, match="Task scheduler unavailable"):
                service_mod.reprocess_document("reprocess-task-fail")

        # Status should be restored to failed
        session = store.get("reprocess-task-fail")
        assert session is not None
        assert session.status == "failed"

        # File should be preserved
        assert session.file_path is not None
        assert Path(session.file_path).exists()

        store.remove("reprocess-task-fail")


# ─── Discard service tests ───

class TestDiscardService:
    """Test discard_session() service function."""

    def test_discard_success(self) -> None:
        """discard_session removes a failed session from the store."""
        from app.ocr.service import discard_session

        session = OCRSession(
            session_id="discard-success",
            status="failed",
        )
        store.add(session)

        discard_session("discard-success")

        assert store.get("discard-success") is None

    def test_discard_removes_file(self) -> None:
        """discard_session deletes the temp file and removes the session."""
        from app.ocr.service import discard_session

        upload_dir = settings.entity_upload_path("ocr")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file = upload_dir / "discard-file.jpg"
        temp_file.write_bytes(_create_jpeg())

        session = OCRSession(
            session_id="discard-file",
            status="failed",
            file_path=str(temp_file),
        )
        store.add(session)

        discard_session("discard-file")

        # Session removed
        assert store.get("discard-file") is None
        # File deleted
        assert not temp_file.exists()

    def test_discard_nonexistent_session(self) -> None:
        """discard_session raises ValueError for nonexistent session."""
        from app.ocr.service import discard_session

        with pytest.raises(ValueError, match="não encontrada"):
            discard_session("does-not-exist")

    def test_discard_wrong_status(self) -> None:
        """discard_session raises ValueError when session is not failed."""
        from app.ocr.service import discard_session

        session = OCRSession(
            session_id="discard-wrong-status",
            status="completed",
        )
        store.add(session)

        with pytest.raises(ValueError, match="não 'failed'"):
            discard_session("discard-wrong-status")

        # Session should still exist
        retrieved = store.get("discard-wrong-status")
        assert retrieved is not None
        assert retrieved.status == "completed"

        store.remove("discard-wrong-status")

    def test_discard_file_deletion_failure_logged(self, caplog) -> None:
        """If file deletion fails during discard, the session is still removed and the error is logged."""
        import logging
        from app.ocr.service import discard_session

        upload_dir = settings.entity_upload_path("ocr")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file = upload_dir / "discard-fail-delete.jpg"
        temp_file.write_bytes(_create_jpeg())

        session = OCRSession(
            session_id="discard-fail-delete",
            status="failed",
            file_path=str(temp_file),
        )
        store.add(session)

        # Make the file undeletable by patching Path.unlink
        with patch("pathlib.Path.unlink", side_effect=OSError("Permission denied")):
            caplog.set_level(logging.WARNING)
            discard_session("discard-fail-delete")

        # Session should still be removed despite file deletion failure
        assert store.get("discard-fail-delete") is None

        # Warning should be logged
        assert any("Failed to delete" in record.message for record in caplog.records)

        # Clean up the file manually since unlink was patched
        if temp_file.exists():
            temp_file.unlink()


# ─── Retry endpoint integration tests ───

class TestRetryEndpoint:
    """Integration tests for POST /ocr/{session_id}/retry endpoint."""

    def test_retry_success_returns_202(self, client: TestClient) -> None:
        """Retry endpoint returns 202 when reprocessing a failed session."""
        headers = _get_auth_headers(client)

        # Create a failed session with a real temp file
        upload_dir = settings.entity_upload_path("ocr")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file = upload_dir / "retry-endpoint-success.jpg"
        temp_file.write_bytes(_create_jpeg())

        session = OCRSession(
            session_id="retry-endpoint-success",
            status="failed",
            file_path=str(temp_file),
            file_mime_type="image/jpeg",
        )
        store.add(session)

        def mock_create_task(coro, *args, **kwargs):
            coro.close()
            return MagicMock()

        with patch("app.ocr.service.asyncio.create_task", side_effect=mock_create_task):
            resp = client.post(
                f"/api/v1/ocr/retry-endpoint-success/retry",
                headers=headers,
            )

        assert resp.status_code == 202

        # Session should be claimed (failed -> pending)
        session = store.get("retry-endpoint-success")
        assert session is not None
        assert session.status == "pending"

        store.remove("retry-endpoint-success")

    def test_retry_nonexistent_session_returns_404(self, client: TestClient) -> None:
        """Retry endpoint returns 404 for nonexistent session."""
        headers = _get_auth_headers(client)

        resp = client.post(
            f"/api/v1/ocr/{uuid4().hex}/retry",
            headers=headers,
        )

        assert resp.status_code == 404

    def test_retry_wrong_status_returns_409(self, client: TestClient) -> None:
        """Retry endpoint returns 409 when session is not in 'failed' status."""
        headers = _get_auth_headers(client)

        session = OCRSession(
            session_id="retry-wrong-status",
            status="completed",
        )
        store.add(session)

        resp = client.post(
            "/api/v1/ocr/retry-wrong-status/retry",
            headers=headers,
        )

        assert resp.status_code == 409

        store.remove("retry-wrong-status")

    def test_retry_missing_file_returns_409(self, client: TestClient) -> None:
        """Retry endpoint returns 409 when temp file is missing."""
        headers = _get_auth_headers(client)

        session = OCRSession(
            session_id="retry-missing-file",
            status="failed",
            file_path="/nonexistent/path/file.jpg",
        )
        store.add(session)

        resp = client.post(
            "/api/v1/ocr/retry-missing-file/retry",
            headers=headers,
        )

        assert resp.status_code == 409

        store.remove("retry-missing-file")

    def test_retry_without_auth_returns_401_or_403(self, client: TestClient) -> None:
        """Retry endpoint returns 401/403 without JWT token."""
        resp = client.post(f"/api/v1/ocr/{uuid4().hex}/retry")
        assert resp.status_code in (401, 403)


# ─── Discard endpoint integration tests ───

class TestDiscardEndpoint:
    """Integration tests for DELETE /ocr/{session_id} endpoint."""

    def test_discard_success_returns_204(self, client: TestClient) -> None:
        """Discard endpoint returns 204 when discarding a failed session."""
        headers = _get_auth_headers(client)

        session = OCRSession(
            session_id="discard-endpoint-success",
            status="failed",
        )
        store.add(session)

        resp = client.delete(
            "/api/v1/ocr/discard-endpoint-success",
            headers=headers,
        )

        assert resp.status_code == 204

        # Session should be removed
        assert store.get("discard-endpoint-success") is None

    def test_discard_with_file_returns_204(self, client: TestClient) -> None:
        """Discard endpoint returns 204 and deletes the temp file."""
        headers = _get_auth_headers(client)

        upload_dir = settings.entity_upload_path("ocr")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_file = upload_dir / "discard-endpoint-file.jpg"
        temp_file.write_bytes(_create_jpeg())

        session = OCRSession(
            session_id="discard-endpoint-file",
            status="failed",
            file_path=str(temp_file),
        )
        store.add(session)

        resp = client.delete(
            "/api/v1/ocr/discard-endpoint-file",
            headers=headers,
        )

        assert resp.status_code == 204
        assert store.get("discard-endpoint-file") is None
        assert not temp_file.exists()

    def test_discard_nonexistent_session_returns_404(self, client: TestClient) -> None:
        """Discard endpoint returns 404 for nonexistent session."""
        headers = _get_auth_headers(client)

        resp = client.delete(
            f"/api/v1/ocr/{uuid4().hex}",
            headers=headers,
        )

        assert resp.status_code == 404

    def test_discard_wrong_status_returns_409(self, client: TestClient) -> None:
        """Discard endpoint returns 409 when session is not in 'failed' status."""
        headers = _get_auth_headers(client)

        session = OCRSession(
            session_id="discard-endpoint-wrong-status",
            status="completed",
        )
        store.add(session)

        resp = client.delete(
            "/api/v1/ocr/discard-endpoint-wrong-status",
            headers=headers,
        )

        assert resp.status_code == 409

        # Session should still exist
        retrieved = store.get("discard-endpoint-wrong-status")
        assert retrieved is not None
        assert retrieved.status == "completed"

        store.remove("discard-endpoint-wrong-status")

    def test_discard_without_auth_returns_401_or_403(self, client: TestClient) -> None:
        """Discard endpoint returns 401/403 without JWT token."""
        resp = client.delete(f"/api/v1/ocr/{uuid4().hex}")
        assert resp.status_code in (401, 403)
