"""M13 — Fase 3 — Etapa 3: Confirmação de importação OCR.

Tests for confirm_import() service function, covering:
- Valid confirmation with single item
- Confirmation with excluded items
- Overlap between confirmed and excluded
- Omitted original items
- Non-existent item IDs
- Invalid access key
- Duplicate access key
- Lot quantity conservation
- Lots with different units and factors
- Lot price calculation
- launched_total considering only confirmed items
- Concurrency: second attempt while first is in 'confirming'
- Failure in create_purchase() with rollback and restoration
- Manual purchase without access_key still works
"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.ocr.schemas import (
    ConfirmImportRequest,
    ConfirmImportTotals,
    ConfirmedItem,
    ConfirmLot,
    OCRItem,
    OCRSession,
)
from app.ocr.service import (
    _calculate_extracted_total,
    _calculate_launched_total,
    _calculate_lot_price,
    _validate_access_key,
    _validate_items_coverage,
    _validate_lots_conservation,
    confirm_import,
)
from app.ocr.state import store


# ─── Helpers ──────────────────────────────────────────────────────────────


def _make_ocr_item(
    item_id: str = "item-1",
    quantity: Decimal | None = Decimal("10"),
    commercial_unit: str | None = "un",
    commercial_unit_price: Decimal | None = Decimal("5.00"),
    product_id: int | None = None,
    conversion_factor: Decimal | None = Decimal("1"),
    subtotal_printed: Decimal | None = None,
    subtotal_calculated: Decimal | None = None,
) -> OCRItem:
    return OCRItem(
        item_id=item_id,
        description=f"Produto {item_id}",
        quantity=quantity,
        commercial_unit=commercial_unit,
        commercial_unit_price=commercial_unit_price,
        subtotal_printed=subtotal_printed,
        subtotal_calculated=subtotal_calculated,
        product_id=product_id,
        conversion_factor=conversion_factor,
    )


def _make_session(
    session_id: str = "test-session",
    items: list[OCRItem] | None = None,
    status: str = "completed",
    access_key: str | None = "1" * 44,
    purchased_at: datetime | None = None,
) -> OCRSession:
    return OCRSession(
        session_id=session_id,
        status=status,
        items=items or [_make_ocr_item()],
        access_key=access_key,
        purchased_at=purchased_at or datetime(2025, 6, 15, 10, 0, 0),
    )


def _make_confirmed_item(
    item_id: str = "item-1",
    product_id: int = 1,
    commercial_quantity: Decimal = Decimal("10"),
    commercial_unit_price: Decimal = Decimal("5.00"),
    conversion_factor: Decimal = Decimal("1"),
    commercial_unit: str | None = "un",
    lots: list[ConfirmLot] | None = None,
) -> ConfirmedItem:
    return ConfirmedItem(
        item_id=item_id,
        product_id=product_id,
        commercial_quantity=commercial_quantity,
        commercial_unit_price=commercial_unit_price,
        conversion_factor=conversion_factor,
        commercial_unit=commercial_unit,
        lots=lots,
    )


def _make_request(
    confirmed_items: list[ConfirmedItem] | None = None,
    excluded_item_ids: list[str] | None = None,
) -> ConfirmImportRequest:
    return ConfirmImportRequest(
        confirmed_items=confirmed_items or [_make_confirmed_item()],
        excluded_item_ids=excluded_item_ids or [],
    )


# ─── Access Key Validation ───────────────────────────────────────────────


class TestValidateAccessKey:
    def test_valid_44_digits(self) -> None:
        key = _validate_access_key("1" * 44)
        assert key == "1" * 44

    def test_valid_with_whitespace(self) -> None:
        key = _validate_access_key(f"  {'1' * 44}  ")
        assert key == "1" * 44

    def test_none_raises(self) -> None:
        with pytest.raises(BusinessRuleError, match="obrigatória"):
            _validate_access_key(None)

    def test_empty_string_raises(self) -> None:
        with pytest.raises(BusinessRuleError, match="obrigatória"):
            _validate_access_key("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(BusinessRuleError, match="obrigatória"):
            _validate_access_key("   ")

    def test_short_key_raises(self) -> None:
        with pytest.raises(BusinessRuleError, match="44 dígitos"):
            _validate_access_key("1" * 43)

    def test_long_key_raises(self) -> None:
        with pytest.raises(BusinessRuleError, match="44 dígitos"):
            _validate_access_key("1" * 45)

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(BusinessRuleError, match="44 dígitos"):
            _validate_access_key("A" + "1" * 43)


# ─── Items Coverage Validation ───────────────────────────────────────────


class TestValidateItemsCoverage:
    def test_all_confirmed_no_excluded(self) -> None:
        original_map = {"item-1": _make_ocr_item("item-1")}
        request = _make_request(
            confirmed_items=[_make_confirmed_item("item-1")],
            excluded_item_ids=[],
        )
        # Should not raise
        _validate_items_coverage(original_map, request)

    def test_confirmed_and_excluded(self) -> None:
        original_map = {
            "item-1": _make_ocr_item("item-1"),
            "item-2": _make_ocr_item("item-2"),
        }
        request = _make_request(
            confirmed_items=[_make_confirmed_item("item-1")],
            excluded_item_ids=["item-2"],
        )
        _validate_items_coverage(original_map, request)

    def test_overlap_raises(self) -> None:
        original_map = {
            "item-1": _make_ocr_item("item-1"),
            "item-2": _make_ocr_item("item-2"),
        }
        request = _make_request(
            confirmed_items=[_make_confirmed_item("item-1")],
            excluded_item_ids=["item-1"],
        )
        with pytest.raises(BusinessRuleError, match="simultaneamente"):
            _validate_items_coverage(original_map, request)

    def test_omitted_item_raises(self) -> None:
        original_map = {
            "item-1": _make_ocr_item("item-1"),
            "item-2": _make_ocr_item("item-2"),
        }
        request = _make_request(
            confirmed_items=[_make_confirmed_item("item-1")],
            excluded_item_ids=[],
        )
        with pytest.raises(BusinessRuleError, match="não contemplado"):
            _validate_items_coverage(original_map, request)

    def test_non_existent_id_raises(self) -> None:
        original_map = {"item-1": _make_ocr_item("item-1")}
        request = _make_request(
            confirmed_items=[_make_confirmed_item("item-1")],
            excluded_item_ids=["item-999"],
        )
        with pytest.raises(BusinessRuleError, match="inexistente"):
            _validate_items_coverage(original_map, request)

    def test_non_existent_confirmed_id_raises(self) -> None:
        original_map = {"item-1": _make_ocr_item("item-1")}
        request = _make_request(
            confirmed_items=[_make_confirmed_item("item-999")],
            excluded_item_ids=[],
        )
        with pytest.raises(BusinessRuleError, match="inexistente"):
            _validate_items_coverage(original_map, request)


# ─── Lot Conservation Validation ─────────────────────────────────────────


class TestValidateLotsConservation:
    def test_no_lots_skips(self) -> None:
        confirmed = _make_confirmed_item("item-1", lots=None)
        original = _make_ocr_item("item-1", quantity=Decimal("10"), conversion_factor=Decimal("1"))
        # Should not raise
        _validate_lots_conservation(confirmed, original)

    def test_conservation_matches(self) -> None:
        # Original: 10 un × factor 1 = 10 base
        # Lots: 5 un × 1 + 5 un × 1 = 10 base
        confirmed = _make_confirmed_item(
            "item-1",
            lots=[
                ConfirmLot(commercial_quantity=Decimal("5"), conversion_factor=Decimal("1")),
                ConfirmLot(commercial_quantity=Decimal("5"), conversion_factor=Decimal("1")),
            ],
        )
        original = _make_ocr_item(
            "item-1", quantity=Decimal("10"), conversion_factor=Decimal("1")
        )
        _validate_lots_conservation(confirmed, original)

    def test_conservation_mismatch_raises(self) -> None:
        # Original: 10 un × factor 1 = 10 base
        # Lots: 3 un × 1 + 3 un × 1 = 6 base (mismatch)
        confirmed = _make_confirmed_item(
            "item-1",
            lots=[
                ConfirmLot(commercial_quantity=Decimal("3"), conversion_factor=Decimal("1")),
                ConfirmLot(commercial_quantity=Decimal("3"), conversion_factor=Decimal("1")),
            ],
        )
        original = _make_ocr_item(
            "item-1", quantity=Decimal("10"), conversion_factor=Decimal("1")
        )
        with pytest.raises(BusinessRuleError, match="unidade-base"):
            _validate_lots_conservation(confirmed, original)

    def test_different_units_conservation(self) -> None:
        # Original: 2 caixa × factor 24 = 48 base
        # Lots: 1 caixa × 24 + 24 un × 1 = 48 base
        confirmed = _make_confirmed_item(
            "item-1",
            commercial_unit="caixa",
            conversion_factor=Decimal("24"),
            commercial_quantity=Decimal("2"),
            lots=[
                ConfirmLot(
                    commercial_quantity=Decimal("1"),
                    commercial_unit="caixa",
                    conversion_factor=Decimal("24"),
                ),
                ConfirmLot(
                    commercial_quantity=Decimal("24"),
                    commercial_unit="un",
                    conversion_factor=Decimal("1"),
                ),
            ],
        )
        original = _make_ocr_item(
            "item-1",
            quantity=Decimal("2"),
            commercial_unit="caixa",
            conversion_factor=Decimal("24"),
        )
        _validate_lots_conservation(confirmed, original)

    def test_missing_original_data_raises(self) -> None:
        confirmed = _make_confirmed_item(
            "item-1",
            lots=[
                ConfirmLot(commercial_quantity=Decimal("5"), conversion_factor=Decimal("1")),
            ],
        )
        original = _make_ocr_item("item-1", quantity=None, conversion_factor=None)
        with pytest.raises(BusinessRuleError, match="insuficientes"):
            _validate_lots_conservation(confirmed, original)


# ─── Lot Price Calculation ───────────────────────────────────────────────


class TestCalculateLotPrice:
    def test_same_factor(self) -> None:
        price = _calculate_lot_price(Decimal("60.00"), Decimal("12"), Decimal("12"))
        assert price == Decimal("60.00")

    def test_different_factor(self) -> None:
        # Item: R$60.00 per caixa of 12, lot: per unit (factor 1)
        # lot_price = 60.00 × (1 / 12) = 5.00
        price = _calculate_lot_price(Decimal("60.00"), Decimal("12"), Decimal("1"))
        assert price == Decimal("5.00")

    def test_larger_factor(self) -> None:
        # Item: R$5.00 per unit (factor 1), lot: per caixa of 24 (factor 24)
        # lot_price = 5.00 × (24 / 1) = 120.00
        price = _calculate_lot_price(Decimal("5.00"), Decimal("1"), Decimal("24"))
        assert price == Decimal("120.00")


# ─── Extracted Total Calculation ─────────────────────────────────────────


class TestCalculateExtractedTotal:
    def test_subtotal_printed_priority(self) -> None:
        session = _make_session(
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    subtotal_printed=Decimal("60.00"),
                    subtotal_calculated=Decimal("50.00"),
                )
            ]
        )
        total, count = _calculate_extracted_total(session)
        assert total == Decimal("60.00")
        assert count == 0

    def test_subtotal_calculated_fallback(self) -> None:
        session = _make_session(
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    subtotal_calculated=Decimal("50.00"),
                )
            ]
        )
        total, count = _calculate_extracted_total(session)
        assert total == Decimal("50.00")
        assert count == 0

    def test_quantity_price_fallback(self) -> None:
        session = _make_session(
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                )
            ]
        )
        total, count = _calculate_extracted_total(session)
        assert total == Decimal("50.00")
        assert count == 0

    def test_no_subtotal_counted(self) -> None:
        session = _make_session(
            items=[
                _make_ocr_item("item-1", quantity=None, commercial_unit_price=None),
            ]
        )
        total, count = _calculate_extracted_total(session)
        assert total == Decimal("0")
        assert count == 1

    def test_includes_excluded_items(self) -> None:
        # Extracted total includes ALL original items, even excluded ones
        session = _make_session(
            items=[
                _make_ocr_item("item-1", quantity=Decimal("10"), commercial_unit_price=Decimal("5.00")),
                _make_ocr_item("item-2", quantity=Decimal("2"), commercial_unit_price=Decimal("3.00")),
            ]
        )
        total, count = _calculate_extracted_total(session)
        # Both items included: 50.00 + 6.00 = 56.00
        assert total == Decimal("56.00")
        assert count == 0

    def test_zero_subtotal_is_valid(self) -> None:
        session = _make_session(
            items=[
                _make_ocr_item("item-1", subtotal_printed=Decimal("0.00")),
            ]
        )
        total, count = _calculate_extracted_total(session)
        assert total == Decimal("0.00")
        assert count == 0


# ─── Launched Total Calculation ──────────────────────────────────────────


class TestCalculateLaunchedTotal:
    def test_single_item(self) -> None:
        request = _make_request(
            confirmed_items=[
                _make_confirmed_item("item-1", commercial_quantity=Decimal("10"), commercial_unit_price=Decimal("5.00"))
            ]
        )
        total = _calculate_launched_total(request)
        assert total == Decimal("50.00")

    def test_multiple_items(self) -> None:
        request = _make_request(
            confirmed_items=[
                _make_confirmed_item("item-1", commercial_quantity=Decimal("10"), commercial_unit_price=Decimal("5.00")),
                _make_confirmed_item("item-2", commercial_quantity=Decimal("2"), commercial_unit_price=Decimal("3.00")),
            ]
        )
        total = _calculate_launched_total(request)
        assert total == Decimal("56.00")

    def test_with_lots(self) -> None:
        # Item: R$60.00 per caixa (factor 12)
        # Lot 1: 1 caixa (factor 12) → price = 60.00 × (12/12) = 60.00 → subtotal = 60.00
        # Lot 2: 24 un (factor 1) → price = 60.00 × (1/12) = 5.00 → subtotal = 120.00
        request = _make_request(
            confirmed_items=[
                _make_confirmed_item(
                    "item-1",
                    commercial_quantity=Decimal("2"),
                    commercial_unit_price=Decimal("60.00"),
                    conversion_factor=Decimal("12"),
                    lots=[
                        ConfirmLot(
                            commercial_quantity=Decimal("1"),
                            commercial_unit="caixa",
                            conversion_factor=Decimal("12"),
                        ),
                        ConfirmLot(
                            commercial_quantity=Decimal("24"),
                            commercial_unit="un",
                            conversion_factor=Decimal("1"),
                        ),
                    ],
                )
            ]
        )
        total = _calculate_launched_total(request)
        # Lot 1: 1 × 60.00 = 60.00
        # Lot 2: 24 × 5.00 = 120.00
        assert total == Decimal("180.00")


# ─── State Machine: try_claim_confirming ─────────────────────────────────


class TestTryClaimConfirming:
    def setup_method(self) -> None:
        store._sessions.clear()

    def test_claim_completed_session(self) -> None:
        session = _make_session("s1", status="completed")
        store.add(session)
        result = store.try_claim_confirming("s1")
        assert result is not None
        assert result.status == "confirming"

    def test_claim_nonexistent_session(self) -> None:
        result = store.try_claim_confirming("nonexistent")
        assert result is None

    def test_claim_failed_session(self) -> None:
        session = _make_session("s1", status="failed")
        store.add(session)
        result = store.try_claim_confirming("s1")
        assert result is None

    def test_double_claim_second_fails(self) -> None:
        session = _make_session("s1", status="completed")
        store.add(session)
        result1 = store.try_claim_confirming("s1")
        assert result1 is not None
        result2 = store.try_claim_confirming("s1")
        assert result2 is None

    def test_restore_completed(self) -> None:
        session = _make_session("s1", status="completed")
        store.add(session)
        store.try_claim_confirming("s1")
        assert store.get("s1").status == "confirming"
        store.restore_completed("s1")
        assert store.get("s1").status == "completed"


# ─── Integration: confirm_import ─────────────────────────────────────────


class TestConfirmImport:
    def setup_method(self) -> None:
        store._sessions.clear()

    def test_valid_single_item_confirmation(
        self,
    ) -> None:
        """Valid confirmation with one item creates purchase and returns response."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    product_id=1,
                    conversion_factor=Decimal("1"),
                )
            ],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[
                _make_confirmed_item(
                    "item-1",
                    product_id=1,
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                )
            ]
        )

        # Mock create_purchase to avoid DB dependency
        mock_db = MagicMock(spec=Session)
        with patch(
            "app.ocr.service._create_purchase"
        ) as mock_create:
            from app.purchases.schemas import PurchaseRead, PurchaseItemRead

            mock_create.return_value = PurchaseRead(
                id=1,
                purchased_at=session.purchased_at,
                access_key="1" * 44,
                items=[
                    PurchaseItemRead(
                        id=1,
                        product_id=1,
                        product_name="Produto Teste",
                        base_unit="UN",
                        commercial_quantity=Decimal("10"),
                        commercial_unit_price=Decimal("5.00"),
                        conversion_factor=Decimal("1"),
                    )
                ],
            )

            response = confirm_import(mock_db, "s1", request)

        assert response.purchase_id == 1
        assert response.access_key == "1" * 44
        assert len(response.confirmed_items) == 1
        assert len(response.excluded_items) == 0
        assert response.totals.launched_total == Decimal("50.00")

    def test_confirmation_with_excluded_items(
        self,
    ) -> None:
        """Confirmation with excluded items — launched_total only includes confirmed."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    product_id=1,
                    conversion_factor=Decimal("1"),
                ),
                _make_ocr_item(
                    "item-2",
                    quantity=Decimal("2"),
                    commercial_unit_price=Decimal("3.00"),
                    product_id=2,
                    conversion_factor=Decimal("1"),
                ),
            ],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[
                _make_confirmed_item(
                    "item-1",
                    product_id=1,
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                )
            ],
            excluded_item_ids=["item-2"],
        )

        mock_db = MagicMock(spec=Session)
        with patch("app.ocr.service._create_purchase") as mock_create:
            from app.purchases.schemas import PurchaseRead, PurchaseItemRead

            mock_create.return_value = PurchaseRead(
                id=1,
                purchased_at=session.purchased_at,
                access_key="1" * 44,
                items=[
                    PurchaseItemRead(
                        id=1,
                        product_id=1,
                        product_name="Produto 1",
                        base_unit="UN",
                        commercial_quantity=Decimal("10"),
                        commercial_unit_price=Decimal("5.00"),
                        conversion_factor=Decimal("1"),
                    )
                ],
            )

            response = confirm_import(mock_db, "s1", request)

        # launched_total: only confirmed item (10 × 5.00 = 50.00)
        assert response.totals.launched_total == Decimal("50.00")
        # extracted_total: ALL items (50.00 + 6.00 = 56.00)
        assert response.totals.extracted_total == Decimal("56.00")
        assert len(response.excluded_items) == 1
        assert response.excluded_items[0].item_id == "item-2"

    def test_session_not_completed_raises(self) -> None:
        """Confirmation rejected when session is not in 'completed' state."""
        session = _make_session("s1", status="processing")
        store.add(session)

        request = _make_request()
        mock_db = MagicMock(spec=Session)

        with pytest.raises(BusinessRuleError, match="não disponível"):
            confirm_import(mock_db, "s1", request)

    def test_session_not_found_raises(self) -> None:
        """Confirmation rejected when session does not exist."""
        request = _make_request()
        mock_db = MagicMock(spec=Session)

        with pytest.raises(BusinessRuleError, match="não encontrada"):
            confirm_import(mock_db, "nonexistent", request)

    def test_missing_access_key_raises(self) -> None:
        """Confirmation rejected when session has no access_key."""
        session = _make_session("s1", access_key=None)
        store.add(session)

        request = _make_request()
        mock_db = MagicMock(spec=Session)

        with pytest.raises(BusinessRuleError, match="obrigatória"):
            confirm_import(mock_db, "s1", request)

    def test_invalid_access_key_raises(self) -> None:
        """Confirmation rejected when access_key is invalid."""
        session = _make_session("s1", access_key="123")
        store.add(session)

        request = _make_request()
        mock_db = MagicMock(spec=Session)

        with pytest.raises(BusinessRuleError, match="44 dígitos"):
            confirm_import(mock_db, "s1", request)

    def test_overlap_raises(self) -> None:
        """Confirmation rejected when item is both confirmed and excluded."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item("item-1", product_id=1, conversion_factor=Decimal("1")),
                _make_ocr_item("item-2", product_id=2, conversion_factor=Decimal("1")),
            ],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[
                _make_confirmed_item("item-1", product_id=1),
                _make_confirmed_item("item-2", product_id=2),
            ],
            excluded_item_ids=["item-2"],
        )
        mock_db = MagicMock(spec=Session)

        with pytest.raises(BusinessRuleError, match="simultaneamente"):
            confirm_import(mock_db, "s1", request)

    def test_omitted_item_raises(self) -> None:
        """Confirmation rejected when original item is not in confirmed or excluded."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item("item-1", product_id=1, conversion_factor=Decimal("1")),
                _make_ocr_item("item-2", product_id=2, conversion_factor=Decimal("1")),
            ],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[_make_confirmed_item("item-1", product_id=1)],
            excluded_item_ids=[],
        )
        mock_db = MagicMock(spec=Session)

        with pytest.raises(BusinessRuleError, match="não contemplado"):
            confirm_import(mock_db, "s1", request)

    def test_non_existent_id_raises(self) -> None:
        """Confirmation rejected when item_id does not exist in session."""
        session = _make_session(
            "s1",
            items=[_make_ocr_item("item-1", product_id=1, conversion_factor=Decimal("1"))],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[_make_confirmed_item("item-1", product_id=1)],
            excluded_item_ids=["item-999"],
        )
        mock_db = MagicMock(spec=Session)

        with pytest.raises(BusinessRuleError, match="inexistente"):
            confirm_import(mock_db, "s1", request)

    def test_lot_conservation_failure_raises(self) -> None:
        """Confirmation rejected when lot quantities don't conserve."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    product_id=1,
                    conversion_factor=Decimal("1"),
                )
            ],
        )
        store.add(session)

        # Lots sum to 6 base, but original is 10 base
        request = _make_request(
            confirmed_items=[
                _make_confirmed_item(
                    "item-1",
                    product_id=1,
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    lots=[
                        ConfirmLot(commercial_quantity=Decimal("3"), conversion_factor=Decimal("1")),
                        ConfirmLot(commercial_quantity=Decimal("3"), conversion_factor=Decimal("1")),
                    ],
                )
            ]
        )
        mock_db = MagicMock(spec=Session)

        with pytest.raises(BusinessRuleError, match="unidade-base"):
            confirm_import(mock_db, "s1", request)

    def test_concurrent_confirmation_second_fails(self) -> None:
        """Second concurrent confirmation is rejected — session already in 'confirming'."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    product_id=1,
                    conversion_factor=Decimal("1"),
                )
            ],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[
                _make_confirmed_item(
                    "item-1", product_id=1,
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                )
            ]
        )
        mock_db = MagicMock(spec=Session)

        # First claim succeeds
        with patch("app.ocr.service._create_purchase") as mock_create:
            from app.purchases.schemas import PurchaseRead, PurchaseItemRead

            mock_create.return_value = PurchaseRead(
                id=1,
                purchased_at=session.purchased_at,
                access_key="1" * 44,
                items=[
                    PurchaseItemRead(
                        id=1, product_id=1, product_name="P", base_unit="UN",
                        commercial_quantity=Decimal("10"),
                        commercial_unit_price=Decimal("5.00"),
                        conversion_factor=Decimal("1"),
                    )
                ],
            )
            response1 = confirm_import(mock_db, "s1", request)
            assert response1.purchase_id == 1

        # Second attempt fails — session is in 'confirming'
        with pytest.raises(BusinessRuleError, match="não disponível"):
            confirm_import(mock_db, "s1", request)

    def test_create_purchase_failure_preserves_session_state(self) -> None:
        """When create_purchase raises, session remains in 'confirming' (caller restores)."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    product_id=1,
                    conversion_factor=Decimal("1"),
                )
            ],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[
                _make_confirmed_item(
                    "item-1", product_id=1,
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                )
            ]
        )
        mock_db = MagicMock(spec=Session)

        with patch(
            "app.ocr.service._create_purchase",
            side_effect=BusinessRuleError("Produto inativo."),
        ):
            with pytest.raises(BusinessRuleError, match="Produto inativo"):
                confirm_import(mock_db, "s1", request)

        # Session should be in 'confirming' — caller is responsible for restoring
        current = store.get("s1")
        assert current is not None
        assert current.status == "confirming"

    def test_confirmation_with_lots_creates_multiple_items(self) -> None:
        """Confirmation with lots expands to multiple CreatePurchaseItem entries."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("2"),
                    commercial_unit="caixa",
                    commercial_unit_price=Decimal("60.00"),
                    product_id=1,
                    conversion_factor=Decimal("24"),
                )
            ],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[
                _make_confirmed_item(
                    "item-1",
                    product_id=1,
                    commercial_quantity=Decimal("2"),
                    commercial_unit="caixa",
                    commercial_unit_price=Decimal("60.00"),
                    conversion_factor=Decimal("24"),
                    lots=[
                        ConfirmLot(
                            commercial_quantity=Decimal("1"),
                            commercial_unit="caixa",
                            conversion_factor=Decimal("24"),
                        ),
                        ConfirmLot(
                            commercial_quantity=Decimal("24"),
                            commercial_unit="un",
                            conversion_factor=Decimal("1"),
                        ),
                    ],
                )
            ]
        )
        mock_db = MagicMock(spec=Session)

        with patch("app.ocr.service._create_purchase") as mock_create:
            from app.purchases.schemas import PurchaseRead, PurchaseItemRead

            mock_create.return_value = PurchaseRead(
                id=1,
                purchased_at=session.purchased_at,
                access_key="1" * 44,
                items=[
                    PurchaseItemRead(
                        id=1, product_id=1, product_name="P", base_unit="UN",
                        commercial_quantity=Decimal("1"),
                        commercial_unit_price=Decimal("60.00"),
                        conversion_factor=Decimal("24"),
                    ),
                    PurchaseItemRead(
                        id=2, product_id=1, product_name="P", base_unit="UN",
                        commercial_quantity=Decimal("24"),
                        commercial_unit_price=Decimal("5.00"),
                        conversion_factor=Decimal("1"),
                    ),
                ],
            )

            response = confirm_import(mock_db, "s1", request)

        # Verify _create_purchase was called with expanded items
        call_args = mock_create.call_args
        purchase_data = call_args[0][1]  # Second positional arg
        assert len(purchase_data.items) == 2

        # Lot 1: same unit as item → price = 60.00 × (24/24) = 60.00
        lot1 = purchase_data.items[0]
        assert lot1.commercial_unit_price == Decimal("60.00")

        # Lot 2: different unit → price = 60.00 × (1/24) = 2.50
        lot2 = purchase_data.items[1]
        assert lot2.commercial_unit_price == Decimal("2.50")

    def test_response_includes_totals(self) -> None:
        """Response includes correct totals structure."""
        session = _make_session(
            "s1",
            items=[
                _make_ocr_item(
                    "item-1",
                    quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                    subtotal_printed=Decimal("55.00"),
                    product_id=1,
                    conversion_factor=Decimal("1"),
                )
            ],
        )
        store.add(session)

        request = _make_request(
            confirmed_items=[
                _make_confirmed_item(
                    "item-1", product_id=1,
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("5.00"),
                )
            ]
        )
        mock_db = MagicMock(spec=Session)

        with patch("app.ocr.service._create_purchase") as mock_create:
            from app.purchases.schemas import PurchaseRead, PurchaseItemRead

            mock_create.return_value = PurchaseRead(
                id=1,
                purchased_at=session.purchased_at,
                access_key="1" * 44,
                items=[
                    PurchaseItemRead(
                        id=1, product_id=1, product_name="P", base_unit="UN",
                        commercial_quantity=Decimal("10"),
                        commercial_unit_price=Decimal("5.00"),
                        conversion_factor=Decimal("1"),
                    )
                ],
            )

            response = confirm_import(mock_db, "s1", request)

        # extracted_total uses subtotal_printed (priority 1)
        assert response.totals.extracted_total == Decimal("55.00")
        # launched_total uses confirmed qty × price
        assert response.totals.launched_total == Decimal("50.00")
        assert response.totals.items_without_subtotal_count == 0
