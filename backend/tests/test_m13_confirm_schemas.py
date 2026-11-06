"""M13 Phase 3 Step 2 — Confirmation Schema Unit Tests.

Tests the confirmation schemas without depending on service, database, or endpoint:
- ConfirmLot: valid payload, invalid quantity, invalid conversion factor
- ConfirmedItem: valid payload, missing required fields, invalid values
- ConfirmImportRequest: valid payload, empty confirmed_items, duplicate excluded_item_ids
- ConfirmImportTotals: serialization of totals
- ConfirmImportResponse: full response serialization
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.ocr.schemas import (
    ConfirmImportRequest,
    ConfirmImportResponse,
    ConfirmImportTotals,
    ConfirmLot,
    ConfirmedItem,
    ConfirmedItemRead,
    ExcludedItemRead,
)


# ─── ConfirmLot ──────────────────────────────────────────────────────────


class TestConfirmLot:
    """Tests for ConfirmLot schema."""

    def test_valid_lot(self) -> None:
        """A valid lot with quantity, conversion factor, and expiry date."""
        lot = ConfirmLot(
            commercial_quantity=Decimal("10"),
            commercial_unit="DX",
            conversion_factor=Decimal("100"),
            expiry_date=date(2027, 6, 15),
        )
        assert lot.commercial_quantity == Decimal("10")
        assert lot.commercial_unit == "DX"
        assert lot.conversion_factor == Decimal("100")
        assert lot.expiry_date == date(2027, 6, 15)

    def test_valid_lot_without_optional_fields(self) -> None:
        """A valid lot with only required fields."""
        lot = ConfirmLot(
            commercial_quantity=Decimal("5"),
            conversion_factor=Decimal("1"),
        )
        assert lot.commercial_unit is None
        assert lot.expiry_date is None

    def test_reject_zero_quantity(self) -> None:
        """Lot with zero quantity is rejected."""
        with pytest.raises(Exception):
            ConfirmLot(
                commercial_quantity=Decimal("0"),
                conversion_factor=Decimal("1"),
            )

    def test_reject_negative_quantity(self) -> None:
        """Lot with negative quantity is rejected."""
        with pytest.raises(Exception):
            ConfirmLot(
                commercial_quantity=Decimal("-5"),
                conversion_factor=Decimal("1"),
            )

    def test_reject_zero_conversion_factor(self) -> None:
        """Lot with zero conversion factor is rejected."""
        with pytest.raises(Exception):
            ConfirmLot(
                commercial_quantity=Decimal("5"),
                conversion_factor=Decimal("0"),
            )

    def test_reject_negative_conversion_factor(self) -> None:
        """Lot with negative conversion factor is rejected."""
        with pytest.raises(Exception):
            ConfirmLot(
                commercial_quantity=Decimal("5"),
                conversion_factor=Decimal("-1"),
            )


# ─── ConfirmedItem ───────────────────────────────────────────────────────


class TestConfirmedItem:
    """Tests for ConfirmedItem schema."""

    def test_valid_item_without_lots(self) -> None:
        """A valid confirmed item without lots."""
        item = ConfirmedItem(
            item_id="item-uuid-1",
            product_id=42,
            commercial_unit="UN",
            conversion_factor=Decimal("1"),
            commercial_quantity=Decimal("10"),
            commercial_unit_price=Decimal("15.50"),
        )
        assert item.item_id == "item-uuid-1"
        assert item.product_id == 42
        assert item.commercial_unit == "UN"
        assert item.conversion_factor == Decimal("1")
        assert item.commercial_quantity == Decimal("10")
        assert item.commercial_unit_price == Decimal("15.50")
        assert item.lots is None

    def test_valid_item_with_lots(self) -> None:
        """A valid confirmed item divided into lots."""
        item = ConfirmedItem(
            item_id="item-uuid-2",
            product_id=10,
            commercial_unit="DX",
            conversion_factor=Decimal("100"),
            commercial_quantity=Decimal("20"),
            commercial_unit_price=Decimal("5.00"),
            lots=[
                ConfirmLot(
                    commercial_quantity=Decimal("10"),
                    commercial_unit="DX",
                    conversion_factor=Decimal("100"),
                    expiry_date=date(2027, 1, 1),
                ),
                ConfirmLot(
                    commercial_quantity=Decimal("10"),
                    commercial_unit="DX",
                    conversion_factor=Decimal("100"),
                    expiry_date=date(2027, 7, 1),
                ),
            ],
        )
        assert len(item.lots) == 2
        assert item.lots[0].expiry_date == date(2027, 1, 1)
        assert item.lots[1].expiry_date == date(2027, 7, 1)

    def test_price_quantized_to_two_decimals(self) -> None:
        """Price is quantized to two decimal places."""
        item = ConfirmedItem(
            item_id="item-uuid-3",
            product_id=1,
            conversion_factor=Decimal("1"),
            commercial_quantity=Decimal("1"),
            commercial_unit_price=Decimal("10.5"),
        )
        assert item.commercial_unit_price == Decimal("10.50")

    def test_reject_missing_item_id(self) -> None:
        """Confirmed item without item_id is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                product_id=1,
                conversion_factor=Decimal("1"),
                commercial_quantity=Decimal("1"),
                commercial_unit_price=Decimal("10.00"),
            )

    def test_reject_missing_product_id(self) -> None:
        """Confirmed item without product_id is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-4",
                conversion_factor=Decimal("1"),
                commercial_quantity=Decimal("1"),
                commercial_unit_price=Decimal("10.00"),
            )

    def test_reject_missing_conversion_factor(self) -> None:
        """Confirmed item without conversion_factor is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-5",
                product_id=1,
                commercial_quantity=Decimal("1"),
                commercial_unit_price=Decimal("10.00"),
            )

    def test_reject_missing_commercial_quantity(self) -> None:
        """Confirmed item without commercial_quantity is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-6",
                product_id=1,
                conversion_factor=Decimal("1"),
                commercial_unit_price=Decimal("10.00"),
            )

    def test_reject_missing_commercial_unit_price(self) -> None:
        """Confirmed item without commercial_unit_price is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-7",
                product_id=1,
                conversion_factor=Decimal("1"),
                commercial_quantity=Decimal("1"),
            )

    def test_reject_zero_quantity(self) -> None:
        """Confirmed item with zero quantity is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-8",
                product_id=1,
                conversion_factor=Decimal("1"),
                commercial_quantity=Decimal("0"),
                commercial_unit_price=Decimal("10.00"),
            )

    def test_reject_negative_quantity(self) -> None:
        """Confirmed item with negative quantity is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-9",
                product_id=1,
                conversion_factor=Decimal("1"),
                commercial_quantity=Decimal("-1"),
                commercial_unit_price=Decimal("10.00"),
            )

    def test_reject_zero_conversion_factor(self) -> None:
        """Confirmed item with zero conversion factor is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-10",
                product_id=1,
                conversion_factor=Decimal("0"),
                commercial_quantity=Decimal("1"),
                commercial_unit_price=Decimal("10.00"),
            )

    def test_reject_negative_price(self) -> None:
        """Confirmed item with negative price is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-11",
                product_id=1,
                conversion_factor=Decimal("1"),
                commercial_quantity=Decimal("1"),
                commercial_unit_price=Decimal("-5.00"),
            )

    def test_accept_zero_price(self) -> None:
        """Confirmed item with zero price is accepted (free item)."""
        item = ConfirmedItem(
            item_id="item-uuid-12",
            product_id=1,
            conversion_factor=Decimal("1"),
            commercial_quantity=Decimal("1"),
            commercial_unit_price=Decimal("0.00"),
        )
        assert item.commercial_unit_price == Decimal("0.00")

    def test_reject_price_with_more_than_two_decimals(self) -> None:
        """Confirmed item with price having more than 2 decimal places is rejected."""
        with pytest.raises(Exception):
            ConfirmedItem(
                item_id="item-uuid-13",
                product_id=1,
                conversion_factor=Decimal("1"),
                commercial_quantity=Decimal("1"),
                commercial_unit_price=Decimal("10.123"),
            )


# ─── ConfirmImportRequest ────────────────────────────────────────────────


class TestConfirmImportRequest:
    """Tests for ConfirmImportRequest schema."""

    def _make_item(self, item_id: str, product_id: int = 1) -> ConfirmedItem:
        return ConfirmedItem(
            item_id=item_id,
            product_id=product_id,
            conversion_factor=Decimal("1"),
            commercial_quantity=Decimal("1"),
            commercial_unit_price=Decimal("10.00"),
        )

    def test_valid_request_with_confirmed_and_excluded(self) -> None:
        """A valid request with confirmed items and excluded item IDs."""
        req = ConfirmImportRequest(
            confirmed_items=[
                self._make_item("item-1"),
                self._make_item("item-2"),
            ],
            excluded_item_ids=["item-3", "item-4"],
        )
        assert len(req.confirmed_items) == 2
        assert len(req.excluded_item_ids) == 2
        assert "item-3" in req.excluded_item_ids

    def test_valid_request_with_only_confirmed(self) -> None:
        """A valid request with only confirmed items (no exclusions)."""
        req = ConfirmImportRequest(
            confirmed_items=[self._make_item("item-1")],
        )
        assert len(req.confirmed_items) == 1
        assert req.excluded_item_ids == []

    def test_valid_request_with_excluded_only(self) -> None:
        """A valid request with one confirmed item and excluded items."""
        req = ConfirmImportRequest(
            confirmed_items=[self._make_item("item-1")],
            excluded_item_ids=["item-2"],
        )
        assert len(req.confirmed_items) == 1
        assert req.excluded_item_ids == ["item-2"]

    def test_reject_empty_confirmed_items(self) -> None:
        """Request with no confirmed items is rejected."""
        with pytest.raises(Exception):
            ConfirmImportRequest(
                confirmed_items=[],
                excluded_item_ids=["item-1"],
            )

    def test_reject_missing_confirmed_items(self) -> None:
        """Request without confirmed_items field is rejected."""
        with pytest.raises(Exception):
            ConfirmImportRequest(  # type: ignore call-arg
                excluded_item_ids=["item-1"],
            )

    def test_reject_duplicate_excluded_item_ids(self) -> None:
        """Request with duplicate excluded item IDs is rejected."""
        with pytest.raises(Exception):
            ConfirmImportRequest(
                confirmed_items=[self._make_item("item-1")],
                excluded_item_ids=["item-2", "item-2"],
            )

    def test_reject_duplicate_confirmed_item_ids(self) -> None:
        """Request with duplicate item_id in confirmed_items is rejected."""
        with pytest.raises(Exception):
            ConfirmImportRequest(
                confirmed_items=[
                    self._make_item("item-dup"),
                    self._make_item("item-dup"),
                ]
            )

    def test_accept_distinct_confirmed_item_ids(self) -> None:
        """Request with distinct item_ids in confirmed_items is accepted."""
        req = ConfirmImportRequest(
            confirmed_items=[
                self._make_item("item-a"),
                self._make_item("item-b"),
                self._make_item("item-c"),
            ]
        )
        assert len(req.confirmed_items) == 3
        ids = [item.item_id for item in req.confirmed_items]
        assert len(ids) == len(set(ids))


# ─── ConfirmImportTotals ─────────────────────────────────────────────────


class TestConfirmImportTotals:
    """Tests for ConfirmImportTotals schema."""

    def test_valid_totals_with_extracted(self) -> None:
        """Totals with all fields populated."""
        totals = ConfirmImportTotals(
            extracted_total=Decimal("150.00"),
            launched_total=Decimal("120.00"),
            items_without_subtotal_count=1,
        )
        assert totals.extracted_total == Decimal("150.00")
        assert totals.launched_total == Decimal("120.00")
        assert totals.items_without_subtotal_count == 1

    def test_valid_totals_without_extracted(self) -> None:
        """Totals with extracted_total as None (not available)."""
        totals = ConfirmImportTotals(
            launched_total=Decimal("100.00"),
        )
        assert totals.extracted_total is None
        assert totals.launched_total == Decimal("100.00")
        assert totals.items_without_subtotal_count == 0

    def test_reject_missing_launched_total(self) -> None:
        """Totals without launched_total is rejected."""
        with pytest.raises(Exception):
            ConfirmImportTotals()  # type: ignore call-arg

    def test_reject_negative_extracted_total(self) -> None:
        """Totals with negative extracted_total is rejected."""
        with pytest.raises(Exception):
            ConfirmImportTotals(
                extracted_total=Decimal("-50.00"),
                launched_total=Decimal("100.00"),
            )

    def test_reject_negative_launched_total(self) -> None:
        """Totals with negative launched_total is rejected."""
        with pytest.raises(Exception):
            ConfirmImportTotals(
                launched_total=Decimal("-100.00"),
            )

    def test_reject_negative_items_without_subtotal_count(self) -> None:
        """Totals with negative items_without_subtotal_count is rejected."""
        with pytest.raises(Exception):
            ConfirmImportTotals(
                launched_total=Decimal("100.00"),
                items_without_subtotal_count=-1,
            )

    def test_accept_extracted_total_none(self) -> None:
        """Totals with extracted_total=None is accepted (OCR did not extract total)."""
        totals = ConfirmImportTotals(
            launched_total=Decimal("100.00"),
        )
        assert totals.extracted_total is None
        assert totals.launched_total == Decimal("100.00")

    def test_accept_zero_values(self) -> None:
        """Totals with zero values are accepted."""
        totals = ConfirmImportTotals(
            extracted_total=Decimal("0.00"),
            launched_total=Decimal("0.00"),
            items_without_subtotal_count=0,
        )
        assert totals.extracted_total == Decimal("0.00")
        assert totals.launched_total == Decimal("0.00")
        assert totals.items_without_subtotal_count == 0


# ─── ConfirmedItemRead ───────────────────────────────────────────────────


class TestConfirmedItemRead:
    """Tests for ConfirmedItemRead schema."""

    def test_serialization(self) -> None:
        """ConfirmedItemRead serializes correctly."""
        item = ConfirmedItemRead(
            item_id="item-uuid-1",
            product_id=42,
            commercial_unit="DX",
            conversion_factor=Decimal("100"),
            commercial_quantity=Decimal("10"),
            commercial_unit_price=Decimal("5.00"),
            expiry_date=date(2027, 6, 15),
            lots=[
                ConfirmLot(
                    commercial_quantity=Decimal("5"),
                    commercial_unit="DX",
                    conversion_factor=Decimal("100"),
                    expiry_date=date(2027, 6, 15),
                )
            ],
        )
        data = item.model_dump()
        assert data["item_id"] == "item-uuid-1"
        assert data["product_id"] == 42
        assert data["commercial_unit"] == "DX"
        assert data["conversion_factor"] == Decimal("100")
        assert data["commercial_quantity"] == Decimal("10")
        assert data["commercial_unit_price"] == Decimal("5.00")
        assert data["expiry_date"] == date(2027, 6, 15)
        assert len(data["lots"]) == 1


# ─── ExcludedItemRead ────────────────────────────────────────────────────


class TestExcludedItemRead:
    """Tests for ExcludedItemRead schema."""

    def test_serialization_with_description(self) -> None:
        """ExcludedItemRead with description."""
        item = ExcludedItemRead(
            item_id="item-uuid-excluded",
            description="Produto X 500g",
        )
        data = item.model_dump()
        assert data["item_id"] == "item-uuid-excluded"
        assert data["description"] == "Produto X 500g"

    def test_serialization_without_description(self) -> None:
        """ExcludedItemRead without description."""
        item = ExcludedItemRead(item_id="item-uuid-excluded")
        data = item.model_dump()
        assert data["item_id"] == "item-uuid-excluded"
        assert data["description"] is None


# ─── ConfirmImportResponse ───────────────────────────────────────────────


class TestConfirmImportResponse:
    """Tests for ConfirmImportResponse schema."""

    def test_full_response_serialization(self) -> None:
        """Full response with confirmed items, excluded items, and totals."""
        resp = ConfirmImportResponse(
            purchase_id=99,
            purchased_at=datetime(2026, 11, 4, 10, 30, 0),
            access_key="12345678901234567890123456789012345678901234",
            confirmed_items=[
                ConfirmedItemRead(
                    item_id="item-1",
                    product_id=1,
                    conversion_factor=Decimal("1"),
                    commercial_quantity=Decimal("10"),
                    commercial_unit_price=Decimal("10.00"),
                )
            ],
            excluded_items=[
                ExcludedItemRead(
                    item_id="item-2",
                    description="Item excluído",
                )
            ],
            totals=ConfirmImportTotals(
                extracted_total=Decimal("150.00"),
                launched_total=Decimal("100.00"),
                items_without_subtotal_count=0,
            ),
        )
        data = resp.model_dump()
        assert data["purchase_id"] == 99
        assert data["access_key"] == "12345678901234567890123456789012345678901234"
        assert len(data["confirmed_items"]) == 1
        assert len(data["excluded_items"]) == 1
        assert data["totals"]["launched_total"] == Decimal("100.00")
        assert data["totals"]["extracted_total"] == Decimal("150.00")

    def test_response_without_access_key(self) -> None:
        """Response without access_key (edge case)."""
        resp = ConfirmImportResponse(
            purchase_id=1,
            purchased_at=datetime(2026, 11, 4),
            confirmed_items=[
                ConfirmedItemRead(
                    item_id="item-1",
                    product_id=1,
                    conversion_factor=Decimal("1"),
                    commercial_quantity=Decimal("1"),
                    commercial_unit_price=Decimal("10.00"),
                )
            ],
            totals=ConfirmImportTotals(launched_total=Decimal("10.00")),
        )
        assert resp.access_key is None

    def test_response_empty_excluded_items(self) -> None:
        """Response with no excluded items defaults to empty list."""
        resp = ConfirmImportResponse(
            purchase_id=1,
            purchased_at=datetime(2026, 11, 4),
            confirmed_items=[
                ConfirmedItemRead(
                    item_id="item-1",
                    product_id=1,
                    conversion_factor=Decimal("1"),
                    commercial_quantity=Decimal("1"),
                    commercial_unit_price=Decimal("10.00"),
                )
            ],
            totals=ConfirmImportTotals(launched_total=Decimal("10.00")),
        )
        assert resp.excluded_items == []

    def test_reject_missing_purchase_id(self) -> None:
        """Response without purchase_id is rejected."""
        with pytest.raises(Exception):
            ConfirmImportResponse(  # type: ignore call-arg
                purchased_at=datetime(2026, 11, 4),
                confirmed_items=[],
                totals=ConfirmImportTotals(launched_total=Decimal("0")),
            )

    def test_reject_missing_purchased_at(self) -> None:
        """Response without purchased_at is rejected."""
        with pytest.raises(Exception):
            ConfirmImportResponse(  # type: ignore call-arg
                purchase_id=1,
                confirmed_items=[],
                totals=ConfirmImportTotals(launched_total=Decimal("0")),
            )

    def test_reject_missing_confirmed_items(self) -> None:
        """Response without confirmed_items is rejected."""
        with pytest.raises(Exception):
            ConfirmImportResponse(  # type: ignore call-arg
                purchase_id=1,
                purchased_at=datetime(2026, 11, 4),
                totals=ConfirmImportTotals(launched_total=Decimal("0")),
            )

    def test_reject_missing_totals(self) -> None:
        """Response without totals is rejected."""
        with pytest.raises(Exception):
            ConfirmImportResponse(  # type: ignore call-arg
                purchase_id=1,
                purchased_at=datetime(2026, 11, 4),
                confirmed_items=[],
            )
