"""M13 — Fase 3 — Etapa 5: Totais no StatusResponse.

Tests for the three financial indicators in the OCR status polling endpoint:
- extracted_total: sum of subtotals of all original items (including excluded).
- launched_total: None before confirmation (only in ConfirmImportResponse).
- items_without_subtotal_count: count of items without available subtotal.

Covers:
- The three fields in StatusResponse.
- extracted_total including all original items.
- Subtotal priority and zero subtotal.
- Count of items without subtotal.
- launched_total before confirmation (None).
- Compatibility with processing and completed sessions.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from app.ocr.schemas import OCRItem, OCRSession
from app.ocr.service import session_to_status_response
from app.ocr.state import store


# ─── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_ocr_sessions():
    """Clean OCR sessions before and after each test."""
    store._sessions.clear()
    yield
    store._sessions.clear()


def _make_item(
    item_id: str = "item-1",
    quantity: Decimal | None = Decimal("10"),
    commercial_unit_price: Decimal | None = Decimal("5.00"),
    subtotal_printed: Decimal | None = None,
    subtotal_calculated: Decimal | None = None,
) -> OCRItem:
    return OCRItem(
        item_id=item_id,
        description=f"Produto {item_id}",
        quantity=quantity,
        commercial_unit_price=commercial_unit_price,
        subtotal_printed=subtotal_printed,
        subtotal_calculated=subtotal_calculated,
    )


def _make_session(
    session_id: str = "test-session",
    status: str = "completed",
    items: list[OCRItem] | None = None,
) -> OCRSession:
    return OCRSession(
        session_id=session_id,
        status=status,
        items=items or [],
        purchased_at=datetime(2025, 6, 15, 10, 0, 0),
        access_key="1" * 44,
    )


# ─── Test: StatusResponse fields ─────────────────────────────────────────


class TestStatusResponseFields:
    """Verify the three financial fields are present in StatusResponse."""

    def test_extracted_total_field_exists(self):
        """extracted_total field is present in the response."""
        session = _make_session(items=[_make_item()])
        result = session_to_status_response(session)
        assert "extracted_total" in result

    def test_launched_total_field_exists(self):
        """launched_total field is present in the response."""
        session = _make_session(items=[_make_item()])
        result = session_to_status_response(session)
        assert "launched_total" in result

    def test_items_without_subtotal_count_field_exists(self):
        """items_without_subtotal_count field is present in the response."""
        session = _make_session(items=[_make_item()])
        result = session_to_status_response(session)
        assert "items_without_subtotal_count" in result


# ─── Test: extracted_total ───────────────────────────────────────────────


class TestExtractedTotal:
    """extracted_total includes all original items."""

    def test_extracted_total_from_quantity_and_price(self):
        """When no subtotal_printed or subtotal_calculated, use qty × price."""
        session = _make_session(items=[
            _make_item(item_id="a", quantity=Decimal("10"), commercial_unit_price=Decimal("5.00")),
            _make_item(item_id="b", quantity=Decimal("6"), commercial_unit_price=Decimal("1.00")),
        ])
        result = session_to_status_response(session)
        # 10 × 5.00 = 50.00, 6 × 1.00 = 6.00 → 56.00
        assert result["extracted_total"] == Decimal("56.00")

    def test_subtotal_printed_priority(self):
        """subtotal_printed takes priority over subtotal_calculated and qty × price."""
        session = _make_session(items=[
            _make_item(
                item_id="a",
                quantity=Decimal("10"),
                commercial_unit_price=Decimal("5.00"),
                subtotal_printed=Decimal("48.00"),
                subtotal_calculated=Decimal("50.00"),
            ),
        ])
        result = session_to_status_response(session)
        # subtotal_printed (48.00) is used, not 50.00
        assert result["extracted_total"] == Decimal("48.00")

    def test_subtotal_calculated_fallback(self):
        """subtotal_calculated is used when subtotal_printed is absent."""
        session = _make_session(items=[
            _make_item(
                item_id="a",
                quantity=Decimal("10"),
                commercial_unit_price=Decimal("5.00"),
                subtotal_calculated=Decimal("49.50"),
            ),
        ])
        result = session_to_status_response(session)
        # subtotal_calculated (49.50) is used, not qty × price (50.00)
        assert result["extracted_total"] == Decimal("49.50")

    def test_zero_subtotal_is_valid(self):
        """A subtotal of zero is valid and contributes to the total."""
        session = _make_session(items=[
            _make_item(
                item_id="a",
                quantity=Decimal("10"),
                commercial_unit_price=Decimal("5.00"),
                subtotal_printed=Decimal("0.00"),
            ),
        ])
        result = session_to_status_response(session)
        assert result["extracted_total"] == Decimal("0.00")

    def test_extracted_total_none_when_no_items(self):
        """extracted_total is None when the session has no items."""
        session = _make_session(items=[])
        result = session_to_status_response(session)
        assert result["extracted_total"] is None

    def test_extracted_total_none_before_completed(self):
        """extracted_total is None when status is 'processing' or 'pending'."""
        session = _make_session(status="processing", items=[_make_item()])
        result = session_to_status_response(session)
        assert result["extracted_total"] is None

        session2 = _make_session(status="pending", items=[_make_item()])
        result2 = session_to_status_response(session2)
        assert result2["extracted_total"] is None


# ─── Test: items_without_subtotal_count ──────────────────────────────────


class TestItemsWithoutSubtotalCount:
    """Count items without available subtotal."""

    def test_no_items_without_subtotal(self):
        """All items have subtotal → count is 0."""
        session = _make_session(items=[
            _make_item(item_id="a", quantity=Decimal("10"), commercial_unit_price=Decimal("5.00")),
        ])
        result = session_to_status_response(session)
        assert result["items_without_subtotal_count"] == 0

    def test_item_without_quantity_counted(self):
        """Item with no quantity and no price is counted."""
        session = _make_session(items=[
            _make_item(item_id="a", quantity=None, commercial_unit_price=Decimal("5.00")),
        ])
        result = session_to_status_response(session)
        assert result["items_without_subtotal_count"] == 1

    def test_item_without_price_counted(self):
        """Item with quantity but no price is counted."""
        session = _make_session(items=[
            _make_item(item_id="a", quantity=Decimal("10"), commercial_unit_price=None),
        ])
        result = session_to_status_response(session)
        assert result["items_without_subtotal_count"] == 1

    def test_item_with_zero_subtotal_not_counted(self):
        """Item with subtotal_printed=0 is NOT counted as without subtotal."""
        session = _make_session(items=[
            _make_item(
                item_id="a",
                quantity=Decimal("10"),
                commercial_unit_price=Decimal("5.00"),
                subtotal_printed=Decimal("0.00"),
            ),
        ])
        result = session_to_status_response(session)
        assert result["items_without_subtotal_count"] == 0

    def test_mixed_items_counted_correctly(self):
        """Only items truly without subtotal are counted."""
        session = _make_session(items=[
            # Has subtotal_printed
            _make_item(item_id="a", subtotal_printed=Decimal("10.00")),
            # Has qty × price
            _make_item(item_id="b", quantity=Decimal("5"), commercial_unit_price=Decimal("2.00")),
            # No subtotal at all
            _make_item(item_id="c", quantity=None, commercial_unit_price=None),
        ])
        result = session_to_status_response(session)
        assert result["items_without_subtotal_count"] == 1
        # extracted_total: 10.00 + 10.00 = 20.00
        assert result["extracted_total"] == Decimal("20.00")

    def test_count_is_zero_when_no_items(self):
        """items_without_subtotal_count is 0 when there are no items."""
        session = _make_session(items=[])
        result = session_to_status_response(session)
        assert result["items_without_subtotal_count"] == 0


# ─── Test: launched_total ────────────────────────────────────────────────


class TestLaunchedTotal:
    """launched_total is None before confirmation."""

    def test_launched_total_none_before_confirmation(self):
        """launched_total is None when session is in 'completed' state (pre-confirmation)."""
        session = _make_session(status="completed", items=[_make_item()])
        result = session_to_status_response(session)
        assert result["launched_total"] is None

    def test_launched_total_none_during_processing(self):
        """launched_total is None when session is in 'processing' state."""
        session = _make_session(status="processing", items=[_make_item()])
        result = session_to_status_response(session)
        assert result["launched_total"] is None

    def test_launched_total_none_during_confirming(self):
        """launched_total is None when session is in 'confirming' state.
        
        'confirming' is a transient internal state not in the OCRStatus Literal,
        so we use model_construct() to create the session.
        """
        session = OCRSession.model_construct(
            session_id="test-confirming",
            status="confirming",
            items=[_make_item()],
            purchased_at=datetime(2025, 6, 15, 10, 0, 0),
            access_key="1" * 44,
        )
        result = session_to_status_response(session)
        assert result["launched_total"] is None


# ─── Test: Status compatibility ──────────────────────────────────────────


class TestStatusCompatibility:
    """Totals behavior across different session statuses."""

    def test_pending_session_has_no_totals(self):
        """Pending session: all totals are None/0."""
        session = _make_session(status="pending", items=[_make_item()])
        result = session_to_status_response(session)
        assert result["extracted_total"] is None
        assert result["launched_total"] is None
        assert result["items_without_subtotal_count"] == 0

    def test_processing_session_has_no_totals(self):
        """Processing session: all totals are None/0."""
        session = _make_session(status="processing", items=[_make_item()])
        result = session_to_status_response(session)
        assert result["extracted_total"] is None
        assert result["launched_total"] is None
        assert result["items_without_subtotal_count"] == 0

    def test_completed_session_has_extracted_total(self):
        """Completed session: extracted_total is calculated."""
        session = _make_session(status="completed", items=[
            _make_item(item_id="a", quantity=Decimal("10"), commercial_unit_price=Decimal("5.00")),
        ])
        result = session_to_status_response(session)
        assert result["extracted_total"] == Decimal("50.00")
        assert result["launched_total"] is None
        assert result["items_without_subtotal_count"] == 0

    def test_failed_session_has_no_totals(self):
        """Failed session: all totals are None/0."""
        session = _make_session(status="failed", items=[_make_item()])
        result = session_to_status_response(session)
        assert result["extracted_total"] is None
        assert result["launched_total"] is None
        assert result["items_without_subtotal_count"] == 0

    def test_confirming_session_has_extracted_total(self):
        """Confirming session: extracted_total is calculated (during confirmation).
        
        'confirming' is a transient internal state not in the OCRStatus Literal,
        so we use model_construct() to create the session.
        """
        session = OCRSession.model_construct(
            session_id="test-confirming-total",
            status="confirming",
            items=[
                _make_item(item_id="a", quantity=Decimal("10"), commercial_unit_price=Decimal("5.00")),
            ],
            purchased_at=datetime(2025, 6, 15, 10, 0, 0),
            access_key="1" * 44,
        )
        result = session_to_status_response(session)
        assert result["extracted_total"] == Decimal("50.00")
        assert result["launched_total"] is None
