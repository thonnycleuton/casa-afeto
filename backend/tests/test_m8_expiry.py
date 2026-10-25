"""M8 — Expiry Management tests.

Covers acceptance criteria AC-M8-001 to AC-M8-024.
Frontend ACs (017-019) are excluded — no frontend test automation.
"""
from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.inventory.batch_service import calculate_expiry_status, consume_fifo
from app.inventory.models import StockBatch
from app.products.models import InventoryMovement, Product


def _make_product(client: TestClient, register: Callable[[int], None]) -> dict[str, Any]:
    payload = {"name": f"prod-{uuid4().hex[:8]}", "base_unit": "UN"}
    res = client.post("/api/v1/products", json=payload)
    assert res.status_code == 201
    data = res.json()
    register(data["id"])
    return data


def _entry(
    client: TestClient,
    product_id: int,
    quantity: str,
    unit_cost: str | None = None,
    expiry_date: str | None = None,
) -> dict:
    payload: dict[str, Any] = {"quantity": quantity}
    if unit_cost is not None:
        payload["unit_cost"] = unit_cost
    if expiry_date is not None:
        payload["expiry_date"] = expiry_date
    res = client.post(f"/api/v1/products/{product_id}/inventory/entries", json=payload)
    assert res.status_code == 201
    return res.json()


def _get_batches(
    client: TestClient, product_id: int, include_exhausted: bool = False
) -> list[dict]:
    params = {"include_exhausted": include_exhausted}
    res = client.get(f"/api/v1/products/{product_id}/batches", params=params)
    assert res.status_code == 200
    return res.json()


def _get_expiry_alerts(
    client: TestClient,
    threshold_days: int = 7,
    include_expired: bool = True,
) -> list[dict]:
    params = {
        "threshold_days": threshold_days,
        "include_expired": include_expired,
    }
    res = client.get("/api/v1/inventory/expiry-alerts", params=params)
    assert res.status_code == 200
    return res.json()


# ─── AC-M8-001: Batch with expiry_date ───

def test_batch_created_with_expiry_date(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-001: Manual ENTRY with expiry_date creates a batch with that date."""
    product = _make_product(client, register_product_for_cleanup)
    future = (date.today() + timedelta(days=30)).isoformat()
    _entry(client, product["id"], "10", "5.00", future)

    batches = _get_batches(client, product["id"])
    assert len(batches) == 1
    assert batches[0]["expiry_date"] == future


# ─── AC-M8-002: Batch without expiry_date ───

def test_batch_created_without_expiry_date(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-002: Manual ENTRY without expiry_date creates a batch with NULL."""
    product = _make_product(client, register_product_for_cleanup)
    _entry(client, product["id"], "10", "5.00")

    batches = _get_batches(client, product["id"])
    assert len(batches) == 1
    assert batches[0]["expiry_date"] is None


# ─── AC-M8-003: Expiry inherited from purchase ───

def test_expiry_inherited_from_purchase(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-003: Purchase item with expiry_date creates a batch with that date."""
    product = _make_product(client, register_product_for_cleanup)
    future = (date.today() + timedelta(days=60)).isoformat()

    payload = {
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "10",
                "commercial_unit_price": "5.00",
                "expiry_date": future,
            }
        ]
    }
    res = client.post("/api/v1/purchases", json=payload)
    assert res.status_code == 201

    batches = _get_batches(client, product["id"])
    assert len(batches) == 1
    assert batches[0]["expiry_date"] == future


# ─── AC-M8-004: Expiry date is immutable ───

def test_expiry_date_is_immutable(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-004: Once a batch is created, its expiry_date cannot be changed.

    The API does not expose a PATCH endpoint for batches, so immutability is
    guaranteed by design. We verify the batch API only supports GET.
    """
    product = _make_product(client, register_product_for_cleanup)
    future = (date.today() + timedelta(days=30)).isoformat()
    _entry(client, product["id"], "10", "5.00", future)

    batches = _get_batches(client, product["id"])
    batch_id = batches[0]["id"]

    # PATCH on batch should return 405 (Method Not Allowed)
    res = client.patch(
        f"/api/v1/products/{product['id']}/batches/{batch_id}",
        json={"expiry_date": "2099-01-01"},
    )
    assert res.status_code == 405


# ─── AC-M8-005: FEFO — consume soonest expiry first ───

def test_fefo_consume_soonest_expiry_first(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-005: FEFO consumes the batch with the soonest expiry first."""
    product = _make_product(client, register_product_for_cleanup)
    soon = (date.today() + timedelta(days=5)).isoformat()
    later = (date.today() + timedelta(days=30)).isoformat()

    # Create batch A (expires sooner)
    _entry(client, product["id"], "10", "5.00", soon)
    # Create batch B (expires later)
    _entry(client, product["id"], "10", "5.00", later)

    # Consume 5 units via consume_fifo (FEFO)
    with SessionLocal() as db:
        consumed = consume_fifo(db, product["id"], Decimal("5"))
        db.commit()

    batches = _get_batches(client, product["id"])
    # Batch A (soonest expiry) should be consumed first
    batch_a = [b for b in batches if b["expiry_date"] == soon][0]
    batch_b = [b for b in batches if b["expiry_date"] == later][0]
    assert Decimal(batch_a["quantity_remaining"]) == Decimal("5")
    assert Decimal(batch_b["quantity_remaining"]) == Decimal("10")


# ─── AC-M8-006: FEFO — batch with expiry consumed before NULL ───

def test_fefo_expiry_before_null(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-006: Batch with expiry_date is consumed before batch without."""
    product = _make_product(client, register_product_for_cleanup)
    soon = (date.today() + timedelta(days=5)).isoformat()

    # Batch A: has expiry
    _entry(client, product["id"], "10", "5.00", soon)
    # Batch B: no expiry
    _entry(client, product["id"], "10", "5.00")

    # Consume 5 units via consume_fifo (FEFO)
    with SessionLocal() as db:
        consumed = consume_fifo(db, product["id"], Decimal("5"))
        db.commit()

    batches = _get_batches(client, product["id"])
    batch_a = [b for b in batches if b["expiry_date"] == soon][0]
    batch_b = [b for b in batches if b["expiry_date"] is None][0]
    assert Decimal(batch_a["quantity_remaining"]) == Decimal("5")
    assert Decimal(batch_b["quantity_remaining"]) == Decimal("10")


# ─── AC-M8-007: FEFO — FIFO fallback for NULL expiry ───

def test_fefo_fifo_fallback_for_null_expiry(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-007: Two batches without expiry — FIFO (oldest first) applies."""
    product = _make_product(client, register_product_for_cleanup)

    # Batch A: older (created first)
    _entry(client, product["id"], "10", "5.00")
    # Batch B: newer (created second)
    _entry(client, product["id"], "10", "5.00")

    # Consume 5 units via consume_fifo (FEFO with FIFO fallback)
    with SessionLocal() as db:
        consumed = consume_fifo(db, product["id"], Decimal("5"))
        db.commit()

    batches = _get_batches(client, product["id"])
    # Older batch (first created) should be consumed first
    assert Decimal(batches[0]["quantity_remaining"]) == Decimal("5")
    assert Decimal(batches[1]["quantity_remaining"]) == Decimal("10")


# ─── AC-M8-008: FEFO — cross-batch consumption ───

def test_fefo_cross_batch_consumption(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-008: Consumption spans multiple batches in FEFO order."""
    product = _make_product(client, register_product_for_cleanup)
    soon = (date.today() + timedelta(days=5)).isoformat()
    later = (date.today() + timedelta(days=30)).isoformat()

    # Batch A: 3 units, expires soon
    _entry(client, product["id"], "3", "5.00", soon)
    # Batch B: 10 units, expires later
    _entry(client, product["id"], "10", "5.00", later)

    # Consume 7 units via consume_fifo (FEFO)
    with SessionLocal() as db:
        consumed = consume_fifo(db, product["id"], Decimal("7"))
        db.commit()

    batches = _get_batches(client, product["id"], include_exhausted=True)
    batch_a = [b for b in batches if b["expiry_date"] == soon][0]
    batch_b = [b for b in batches if b["expiry_date"] == later][0]
    assert Decimal(batch_a["quantity_remaining"]) == Decimal("0")
    assert batch_a["status"] == "EXHAUSTED"
    assert Decimal(batch_b["quantity_remaining"]) == Decimal("6")


# ─── AC-M8-009: Expired batch remains ACTIVE ───

def test_expired_batch_remains_active(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-009: A batch past its expiry date stays ACTIVE with EXPIRED status."""
    product = _make_product(client, register_product_for_cleanup)
    past = (date.today() - timedelta(days=5)).isoformat()
    _entry(client, product["id"], "10", "5.00", past)

    batches = _get_batches(client, product["id"])
    assert len(batches) == 1
    assert batches[0]["status"] == "ACTIVE"
    assert batches[0]["expiry_status"] == "EXPIRED"


# ─── AC-M8-010: Warning status for soon expiry ───

def test_warning_status_for_soon_expiry(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-010: Batch expiring within threshold returns WARNING status."""
    product = _make_product(client, register_product_for_cleanup)
    soon = (date.today() + timedelta(days=3)).isoformat()
    _entry(client, product["id"], "10", "5.00", soon)

    batches = _get_batches(client, product["id"])
    assert len(batches) == 1
    assert batches[0]["expiry_status"] == "WARNING"


# ─── AC-M8-011: Expired status via API ───

def test_expired_status_via_api(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-011: Batch past expiry returns EXPIRED status via API."""
    product = _make_product(client, register_product_for_cleanup)
    past = (date.today() - timedelta(days=5)).isoformat()
    _entry(client, product["id"], "10", "5.00", past)

    batches = _get_batches(client, product["id"])
    assert len(batches) == 1
    assert batches[0]["expiry_status"] == "EXPIRED"


# ─── AC-M8-012: No alert for NULL expiry ───

def test_no_alert_for_null_expiry(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-012: Batch without expiry_date does not appear in alerts."""
    product = _make_product(client, register_product_for_cleanup)
    _entry(client, product["id"], "10", "5.00")

    alerts = _get_expiry_alerts(client)
    product_alerts = [a for a in alerts if a["product_id"] == product["id"]]
    assert len(product_alerts) == 0


# ─── AC-M8-013: Global expiry alerts list ───

def test_global_expiry_alerts_list(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-013: GET /inventory/expiry-alerts returns alerts across all products."""
    product_a = _make_product(client, register_product_for_cleanup)
    product_b = _make_product(client, register_product_for_cleanup)

    soon_a = (date.today() + timedelta(days=2)).isoformat()
    soon_b = (date.today() + timedelta(days=5)).isoformat()

    _entry(client, product_a["id"], "10", "5.00", soon_a)
    _entry(client, product_b["id"], "10", "5.00", soon_b)

    alerts = _get_expiry_alerts(client)
    alert_product_ids = {a["product_id"] for a in alerts}
    assert product_a["id"] in alert_product_ids
    assert product_b["id"] in alert_product_ids


# ─── AC-M8-014: Alerts ordered by urgency ───

def test_alerts_ordered_by_urgency(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-014: Alerts are ordered with expired first, then soonest first."""
    product_a = _make_product(client, register_product_for_cleanup)
    product_b = _make_product(client, register_product_for_cleanup)

    past = (date.today() - timedelta(days=5)).isoformat()
    soon = (date.today() + timedelta(days=2)).isoformat()

    _entry(client, product_a["id"], "10", "5.00", past)
    _entry(client, product_b["id"], "10", "5.00", soon)

    alerts = _get_expiry_alerts(client)
    # Filter to only our products
    our_alerts = [a for a in alerts if a["product_id"] in {product_a["id"], product_b["id"]}]
    assert len(our_alerts) == 2
    # Expired (past) should come first
    assert our_alerts[0]["product_id"] == product_a["id"]
    assert our_alerts[0]["expiry_status"] == "EXPIRED"
    # Warning (soon) should come second
    assert our_alerts[1]["product_id"] == product_b["id"]
    assert our_alerts[1]["expiry_status"] == "WARNING"


# ─── AC-M8-015: Expiry on manual entry ───

def test_expiry_on_manual_entry(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-015: Manual inventory entry with expiry_date creates batch with that date."""
    product = _make_product(client, register_product_for_cleanup)
    future = (date.today() + timedelta(days=45)).isoformat()
    _entry(client, product["id"], "10", "5.00", future)

    batches = _get_batches(client, product["id"])
    assert len(batches) == 1
    assert batches[0]["expiry_date"] == future


# ─── AC-M8-016: Expiry per purchase item ───

def test_expiry_per_purchase_item(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-016: Only items with expiry_date inherit it; others stay NULL."""
    product_a = _make_product(client, register_product_for_cleanup)
    product_b = _make_product(client, register_product_for_cleanup)
    future = (date.today() + timedelta(days=60)).isoformat()

    payload = {
        "items": [
            {
                "product_id": product_a["id"],
                "conversion_factor": "1",
                "commercial_quantity": "10",
                "commercial_unit_price": "5.00",
                "expiry_date": future,
            },
            {
                "product_id": product_b["id"],
                "conversion_factor": "1",
                "commercial_quantity": "10",
                "commercial_unit_price": "3.00",
                # No expiry_date
            },
        ]
    }
    res = client.post("/api/v1/purchases", json=payload)
    assert res.status_code == 201

    batches_a = _get_batches(client, product_a["id"])
    batches_b = _get_batches(client, product_b["id"])
    assert batches_a[0]["expiry_date"] == future
    assert batches_b[0]["expiry_date"] is None


# ─── AC-M8-020: Configurable threshold ───

def test_configurable_threshold(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-020: Expiry status changes based on threshold_days parameter."""
    product = _make_product(client, register_product_for_cleanup)
    # Expires in 10 days
    future = (date.today() + timedelta(days=10)).isoformat()
    _entry(client, product["id"], "10", "5.00", future)

    # With threshold=7, 10 days is OK
    alerts_7 = _get_expiry_alerts(client, threshold_days=7)
    product_alerts = [a for a in alerts_7 if a["product_id"] == product["id"]]
    assert len(product_alerts) == 0  # Not within threshold

    # With threshold=14, 10 days is WARNING
    alerts_14 = _get_expiry_alerts(client, threshold_days=14)
    product_alerts = [a for a in alerts_14 if a["product_id"] == product["id"]]
    assert len(product_alerts) == 1
    assert product_alerts[0]["expiry_status"] == "WARNING"


# ─── AC-M8-021: days_until_expiry calculated ───

def test_days_until_expiry_calculated(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-021: days_until_expiry is calculated correctly for future dates."""
    product = _make_product(client, register_product_for_cleanup)
    future = (date.today() + timedelta(days=7)).isoformat()
    _entry(client, product["id"], "10", "5.00", future)

    alerts = _get_expiry_alerts(client)
    product_alerts = [a for a in alerts if a["product_id"] == product["id"]]
    assert len(product_alerts) == 1
    assert product_alerts[0]["days_until_expiry"] == 7


# ─── AC-M8-022: days_until_expiry negative for expired ───

def test_days_until_expiry_negative_for_expired(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-022: days_until_expiry is negative for expired batches."""
    product = _make_product(client, register_product_for_cleanup)
    past = (date.today() - timedelta(days=5)).isoformat()
    _entry(client, product["id"], "10", "5.00", past)

    alerts = _get_expiry_alerts(client)
    product_alerts = [a for a in alerts if a["product_id"] == product["id"]]
    assert len(product_alerts) == 1
    assert product_alerts[0]["days_until_expiry"] == -5


# ─── AC-M8-023: include_expired=false filter ───

def test_include_expired_false_filter(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-023: include_expired=false excludes expired batches from alerts."""
    product_expired = _make_product(client, register_product_for_cleanup)
    product_warning = _make_product(client, register_product_for_cleanup)

    past = (date.today() - timedelta(days=5)).isoformat()
    soon = (date.today() + timedelta(days=3)).isoformat()

    _entry(client, product_expired["id"], "10", "5.00", past)
    _entry(client, product_warning["id"], "10", "5.00", soon)

    # With include_expired=false, only WARNING should appear
    alerts = _get_expiry_alerts(client, include_expired=False)
    alert_ids = {a["product_id"] for a in alerts}
    assert product_expired["id"] not in alert_ids
    assert product_warning["id"] in alert_ids


# ─── AC-M8-024: Migration — existing batches have NULL expiry ───

def test_existing_batches_have_null_expiry(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M8-024: Batches created without expiry_date (M7-style) work correctly.

    The migration adds a nullable column. Existing batches (created without
    expiry_date) should have NULL and continue functioning normally.
    """
    product = _make_product(client, register_product_for_cleanup)
    # Create entry without expiry_date (M7-style)
    _entry(client, product["id"], "10", "5.00")

    batches = _get_batches(client, product["id"])
    assert len(batches) == 1
    assert batches[0]["expiry_date"] is None
    assert batches[0]["expiry_status"] is None
    assert batches[0]["status"] == "ACTIVE"

    # Verify the batch still works for consumption via consume_fifo
    with SessionLocal() as db:
        consumed = consume_fifo(db, product["id"], Decimal("5"))
        db.commit()

    batches = _get_batches(client, product["id"])
    assert Decimal(batches[0]["quantity_remaining"]) == Decimal("5")


# ─── calculate_expiry_status unit tests ───

def test_calculate_expiry_status_expired() -> None:
    """Unit test: calculate_expiry_status returns EXPIRED for past dates."""
    past = date.today() - timedelta(days=5)
    assert calculate_expiry_status(past) == "EXPIRED"


def test_calculate_expiry_status_warning() -> None:
    """Unit test: calculate_expiry_status returns WARNING for within threshold."""
    soon = date.today() + timedelta(days=3)
    assert calculate_expiry_status(soon, threshold_days=7) == "WARNING"


def test_calculate_expiry_status_ok() -> None:
    """Unit test: calculate_expiry_status returns OK for far future."""
    future = date.today() + timedelta(days=30)
    assert calculate_expiry_status(future, threshold_days=7) == "OK"


def test_calculate_expiry_status_none() -> None:
    """Unit test: calculate_expiry_status returns None for NULL expiry."""
    assert calculate_expiry_status(None) is None


def test_calculate_expiry_status_boundary() -> None:
    """Unit test: exactly at threshold returns WARNING."""
    boundary = date.today() + timedelta(days=7)
    assert calculate_expiry_status(boundary, threshold_days=7) == "WARNING"


def test_calculate_expiry_status_day_after_boundary() -> None:
    """Unit test: one day after threshold returns OK."""
    after = date.today() + timedelta(days=8)
    assert calculate_expiry_status(after, threshold_days=7) == "OK"


def test_calculate_expiry_status_today() -> None:
    """Unit test: expiry today returns WARNING (0 days <= threshold)."""
    assert calculate_expiry_status(date.today(), threshold_days=7) == "WARNING"
