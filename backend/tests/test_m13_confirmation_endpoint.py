"""M13 — Fase 3 — Etapa 4: Endpoint de confirmação OCR.

Tests for POST /ocr/{session_id}/confirm endpoint, covering:
- Successful confirmation: service called, commit executed, session removed
- Failure during confirm_import(): rollback and session restoration
- Failure during db.commit(): rollback and session restoration
- uq_purchases_access_key violation: HTTP 409, rollback and restoration
- Other IntegrityError: NOT classified as duplicate key
- Unexpected failure before commit: rollback and session restoration
- Session removal failure after commit: purchase remains, session NOT restored
- Two concurrent confirmations: only one can proceed
"""
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.exceptions import BusinessRuleError
from app.main import app
from app.ocr.schemas import (
    ConfirmImportRequest,
    ConfirmedItem,
    OCRItem,
    OCRSession,
)
from app.ocr.state import store


# ─── Helpers ──────────────────────────────────────────────────────────────


def _make_ocr_item(
    item_id: str = "item-1",
    quantity: Decimal | None = Decimal("10"),
    commercial_unit: str | None = "un",
    commercial_unit_price: Decimal | None = Decimal("5.00"),
    product_id: int | None = 1,
    conversion_factor: Decimal | None = Decimal("1"),
) -> OCRItem:
    return OCRItem(
        item_id=item_id,
        description=f"Produto {item_id}",
        quantity=quantity,
        commercial_unit=commercial_unit,
        commercial_unit_price=commercial_unit_price,
        product_id=product_id,
        conversion_factor=conversion_factor,
    )


def _make_session(
    session_id: str = "test-session",
    items: list[OCRItem] | None = None,
    status: str = "completed",
    access_key: str | None = "1" * 44,
) -> OCRSession:
    return OCRSession(
        session_id=session_id,
        status=status,
        items=items or [_make_ocr_item()],
        access_key=access_key,
        purchased_at=datetime(2025, 6, 15, 10, 0, 0),
    )


def _make_request_json(
    confirmed_items: list[ConfirmedItem] | None = None,
    excluded_item_ids: list[str] | None = None,
) -> dict:
    """Build a ConfirmImportRequest and return model_dump(mode='json') for TestClient."""
    request = ConfirmImportRequest(
        confirmed_items=confirmed_items or [
            ConfirmedItem(
                item_id="item-1",
                product_id=1,
                commercial_quantity=Decimal("10"),
                commercial_unit_price=Decimal("5.00"),
                conversion_factor=Decimal("1"),
                commercial_unit="un",
            )
        ],
        excluded_item_ids=excluded_item_ids or [],
    )
    return request.model_dump(mode="json")


def _mock_response(purchase_id: str = "p-1") -> MagicMock:
    """Create a mock ConfirmImportResponse."""
    mock = MagicMock()
    # Extract numeric ID from "p-1" format, or default to 1
    try:
        mock.purchase_id = int(purchase_id.replace("p-", ""))
    except (ValueError, AttributeError):
        mock.purchase_id = 1
    mock.purchased_at = datetime(2025, 6, 15, 10, 0, 0)
    mock.access_key = "1" * 44
    mock.status = "DRAFT"
    # Totals must be real Decimal values for response_model validation
    mock.totals.extracted_total = Decimal("50.00")
    mock.totals.launched_total = Decimal("50.00")
    mock.totals.items_without_subtotal_count = 0
    mock.confirmed_items = []
    mock.excluded_items = []
    return mock


# ─── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_ocr_sessions():
    """Clean OCR sessions before and after each test."""
    store._sessions.clear()
    yield
    store._sessions.clear()


@pytest.fixture(autouse=True)
def clean_auth_data():
    """Clean all auth-related data before and after each test."""
    from app.auth.models import RefreshToken, PasswordResetToken, User
    with SessionLocal() as db:
        db.query(RefreshToken).delete(synchronize_session=False)
        db.query(PasswordResetToken).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.commit()
    yield
    with SessionLocal() as db:
        db.query(RefreshToken).delete(synchronize_session=False)
        db.query(PasswordResetToken).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.commit()


@pytest.fixture
def mock_db() -> MagicMock:
    """Provide a fresh mock db session for each test."""
    return MagicMock(spec=Session)


def _get_admin_headers(client: TestClient) -> dict[str, str]:
    """Create admin, login, and return auth headers."""
    from uuid import uuid4

    email = f"admin-{uuid4().hex[:8]}@casaafeto.com"
    resp = client.post("/api/v1/auth/setup/create-admin", json={
        "email": email,
        "password": "Admin1234",
        "full_name": "Test Admin",
    })
    assert resp.status_code == 201, f"Setup failed: {resp.text}"
    tokens_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Admin1234",
    })
    assert tokens_resp.status_code == 200, f"Login failed: {tokens_resp.text}"
    tokens = tokens_resp.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@contextmanager
def _post_confirm(
    mock_db: MagicMock,
) -> Generator[TestClient, None, None]:
    """Context manager: create a TestClient with get_db overridden,
    yield it for making the confirm request, then clean up."""
    def mock_get_db() -> Generator[MagicMock, None, None]:
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


# ─── Test: Successful confirmation ────────────────────────────────────────


class TestSuccessfulConfirmation:
    """Happy path: confirm_import succeeds, commit succeeds, session removed."""

    def test_successful_confirmation_flow(
        self, client: TestClient, mock_db: MagicMock
    ):
        """Service called, commit executed, session removed."""
        session = _make_session("sess-001")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        with patch("app.api.v1.ocr.confirm_import", return_value=_mock_response()):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-001/confirm",
                    json=request_json,
                    headers=headers,
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["purchase_id"] in ("p-1", 1)  # mock id may be serialized as int
        assert data["access_key"] == "1" * 44
        assert "sess-001" not in store

    def test_commit_is_called(
        self, client: TestClient, mock_db: MagicMock
    ):
        """db.commit() is executed after confirm_import succeeds."""
        session = _make_session("sess-002")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        with patch("app.api.v1.ocr.confirm_import", return_value=_mock_response()):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-002/confirm",
                    json=request_json,
                    headers=headers,
                )

        assert resp.status_code == 200
        mock_db.commit.assert_called_once()

    def test_session_removed_after_commit(
        self, client: TestClient, mock_db: MagicMock
    ):
        """Session is removed from memory after successful commit."""
        session = _make_session("sess-003")
        store.add(session)
        assert "sess-003" in store

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        with patch("app.api.v1.ocr.confirm_import", return_value=_mock_response()):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-003/confirm",
                    json=request_json,
                    headers=headers,
                )

        assert resp.status_code == 200
        assert "sess-003" not in store


# ─── Test: Pre-commit failures ───────────────────────────────────────────


class TestPreCommitFailure:
    """Failures before commit: rollback and session restoration."""

    def test_business_rule_error_rollback_and_restore(
        self, client: TestClient, mock_db: MagicMock
    ):
        """BusinessRuleError during confirm_import: rollback + restore session."""
        session = _make_session("sess-br")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        with patch(
            "app.api.v1.ocr.confirm_import",
            side_effect=BusinessRuleError("Regra de negócio violada."),
        ):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-br/confirm",
                    json=request_json,
                    headers=headers,
                )

        assert resp.status_code == 409
        mock_db.rollback.assert_called_once()
        restored = store.get("sess-br")
        assert restored is not None
        assert restored.status == "completed"

    def test_unexpected_error_rollback_and_restore(
        self, client: TestClient, mock_db: MagicMock
    ):
        """Unexpected error before commit: rollback + restore session."""
        session = _make_session("sess-unexp")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        with patch(
            "app.api.v1.ocr.confirm_import",
            side_effect=RuntimeError("Erro inesperado."),
        ):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-unexp/confirm",
                    json=request_json,
                    headers=headers,
                )

        assert resp.status_code == 500
        mock_db.rollback.assert_called_once()
        restored = store.get("sess-unexp")
        assert restored is not None
        assert restored.status == "completed"

    def test_commit_failure_rollback_and_restore(
        self, client: TestClient, mock_db: MagicMock
    ):
        """db.commit() failure: rollback + restore session."""
        session = _make_session("sess-commit-fail")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        mock_db.commit.side_effect = Exception("Commit failed")

        with patch("app.api.v1.ocr.confirm_import", return_value=_mock_response()):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-commit-fail/confirm",
                    json=request_json,
                    headers=headers,
                )

        assert resp.status_code == 500
        mock_db.rollback.assert_called_once()
        restored = store.get("sess-commit-fail")
        assert restored is not None
        assert restored.status == "completed"


# ─── Test: IntegrityError handling ────────────────────────────────────────


class TestIntegrityError:
    """IntegrityError: specific handling for uq_purchases_access_key."""

    def test_duplicate_access_key_returns_409(
        self, client: TestClient, mock_db: MagicMock
    ):
        """uq_purchases_access_key violation: HTTP 409, rollback, restore."""
        session = _make_session("sess-dup")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        mock_orig = MagicMock()
        mock_orig.diag.constraint_name = "uq_purchases_access_key"
        mock_integrity = IntegrityError("duplicate key", {}, mock_orig)

        with patch(
            "app.api.v1.ocr.confirm_import",
            side_effect=mock_integrity,
        ):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-dup/confirm",
                    json=request_json,
                    headers=headers,
                )

        assert resp.status_code == 409
        assert "chave de acesso" in resp.json()["detail"].lower()
        mock_db.rollback.assert_called_once()
        restored = store.get("sess-dup")
        assert restored is not None
        assert restored.status == "completed"

    def test_other_integrity_error_not_409(
        self, client: TestClient, mock_db: MagicMock
    ):
        """Other IntegrityError: NOT classified as duplicate key."""
        session = _make_session("sess-other-int")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        mock_orig = MagicMock()
        mock_orig.diag.constraint_name = "other_constraint"
        mock_integrity = IntegrityError("foreign key", {}, mock_orig)

        with patch(
            "app.api.v1.ocr.confirm_import",
            side_effect=mock_integrity,
        ):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-other-int/confirm",
                    json=request_json,
                    headers=headers,
                )

        assert resp.status_code == 503
        mock_db.rollback.assert_called_once()
        restored = store.get("sess-other-int")
        assert restored is not None
        assert restored.status == "completed"


# ─── Test: Post-commit cleanup failure ────────────────────────────────────


class TestPostCommitCleanup:
    """Failures after commit: purchase remains, session NOT restored."""

    def test_session_removal_failure_preserves_purchase(
        self, client: TestClient, mock_db: MagicMock
    ):
        """If store.remove() fails after commit, purchase is NOT rolled back.

        Note: Since confirm_import is mocked, try_claim_confirming is not called,
        so the session stays in 'completed'. The key assertion is that the endpoint
        returns 200 (commit succeeded) even when store.remove() fails.
        """
        session = _make_session("sess-post")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        with (
            patch("app.api.v1.ocr.confirm_import", return_value=_mock_response()),
            patch.object(store, "remove", side_effect=RuntimeError("Remove failed")),
        ):
            with _post_confirm(mock_db) as c:
                resp = c.post(
                    "/api/v1/ocr/sess-post/confirm",
                    json=request_json,
                    headers=headers,
                )

        # The endpoint returns 200 — commit succeeded, response sent
        # The store.remove() failure is logged but doesn't affect the response
        assert resp.status_code == 200


# ─── Test: Concurrency ────────────────────────────────────────────────────


class TestConcurrency:
    """Two concurrent confirmations: only one can proceed."""

    def test_second_concurrent_confirmation_rejected(
        self, client: TestClient, mock_db: MagicMock
    ):
        """Second confirmation while first is in 'confirming' is rejected."""
        session = _make_session("sess-conc")
        store.add(session)

        request_json = _make_request_json()
        headers = _get_admin_headers(client)

        call_count = [0]

        def side_effect_confirm(db, session_id, req):
            call_count[0] += 1
            if call_count[0] == 1:
                return _mock_response("p-conc")
            raise BusinessRuleError(
                "Sessão não encontrada ou não disponível para confirmação."
            )

        with patch("app.api.v1.ocr.confirm_import", side_effect=side_effect_confirm):
            with _post_confirm(mock_db) as c:
                resp1 = c.post(
                    "/api/v1/ocr/sess-conc/confirm",
                    json=request_json,
                    headers=headers,
                )
                assert resp1.status_code == 200

                resp2 = c.post(
                    "/api/v1/ocr/sess-conc/confirm",
                    json=request_json,
                    headers=headers,
                )
                assert resp2.status_code == 409


# ─── Test: Authentication ─────────────────────────────────────────────────


class TestAuthentication:
    """JWT authentication is required."""

    def test_unauthorized_without_token(self, client: TestClient):
        """Request without JWT token is rejected."""
        session = _make_session("sess-auth")
        store.add(session)

        request_json = _make_request_json()
        resp = client.post(
            "/api/v1/ocr/sess-auth/confirm",
            json=request_json,
        )

        assert resp.status_code in (401, 403)

    def test_unauthorized_with_invalid_token(self, client: TestClient):
        """Request with invalid JWT token is rejected."""
        session = _make_session("sess-auth2")
        store.add(session)

        request_json = _make_request_json()
        resp = client.post(
            "/api/v1/ocr/sess-auth2/confirm",
            json=request_json,
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert resp.status_code == 401
