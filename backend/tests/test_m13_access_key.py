"""M13 Phase 3 Step 1 — Access Key Persistence Tests.

Covers the access_key field on Purchase model:
- Validation (44 digits, numeric only)
- Persistence via create_purchase
- Read-back via PurchaseRead
- UNIQUE constraint (uq_purchases_access_key)
- Manual purchases without access_key continue to work
"""
from decimal import Decimal
from typing import Any, Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.purchases.models import Purchase, PurchaseItem


def _create_product(
    client: TestClient,
    register: Callable[[int], None],
    *,
    name: str | None = None,
) -> dict[str, Any]:
    if name is None:
        name = f"m13-test-{uuid4().hex[:8]}"
    resp = client.post("/api/v1/products", json={"name": name, "base_unit": "UN"})
    assert resp.status_code == 201, resp.text
    product = resp.json()
    register(product["id"])
    return product


def _create_purchase(client: TestClient, payload: dict) -> dict:
    resp = client.post("/api/v1/purchases", json=payload)
    if resp.status_code != 201:
        raise AssertionError(f"Purchase creation failed: {resp.status_code} {resp.text}")
    return resp.json()


# ─── AC: Valid 44-digit access_key is persisted ───

def test_access_key_valid_persisted(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """A valid 44-digit access_key is persisted and returned in the response."""
    product = _create_product(client, register_product_for_cleanup)
    access_key = "12345678901234567890123456789012345678901234"  # 44 digits

    purchase = _create_purchase(client, {
        "access_key": access_key,
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    assert purchase["access_key"] == access_key

    # Verify via GET endpoint
    get_resp = client.get(f"/api/v1/purchases/{purchase['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["access_key"] == access_key


# ─── AC: Access key must be exactly 44 digits ───

def test_access_key_reject_short(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """Access key with fewer than 44 digits is rejected."""
    product = _create_product(client, register_product_for_cleanup)

    resp = client.post("/api/v1/purchases", json={
        "access_key": "1234567890123456789012345678901234567890123",  # 43 digits
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    assert resp.status_code == 422
    assert "44 dígitos" in resp.json()["detail"][0]["msg"]


def test_access_key_reject_long(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """Access key with more than 44 digits is rejected."""
    product = _create_product(client, register_product_for_cleanup)

    resp = client.post("/api/v1/purchases", json={
        "access_key": "123456789012345678901234567890123456789012345",  # 45 digits
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    assert resp.status_code == 422
    assert "44 dígitos" in resp.json()["detail"][0]["msg"]


def test_access_key_reject_non_numeric(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """Access key with non-numeric characters is rejected."""
    product = _create_product(client, register_product_for_cleanup)

    resp = client.post("/api/v1/purchases", json={
        "access_key": "1234567890123456789012345678901234567890123a",  # 43 digits + 'a'
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    assert resp.status_code == 422
    assert "44 dígitos" in resp.json()["detail"][0]["msg"]


def test_access_key_reject_unicode_digits(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """Access key with Unicode fullwidth digits (not ASCII 0-9) is rejected.

    str.isdigit() accepts Unicode numerals like fullwidth digits (０-９),
    but the NF-e access key must contain only ASCII digits 0-9.
    """
    product = _create_product(client, register_product_for_cleanup)

    # Fullwidth digits ０-９ look like normal digits but are Unicode characters
    # that pass str.isdigit() but are not ASCII 0-9.
    unicode_key = "０１２３４５６７８９０１２３４５６７８９０１２３４５６７８９０１２３４５６７８９"  # 44 fullwidth digits

    resp = client.post("/api/v1/purchases", json={
        "access_key": unicode_key,
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    assert resp.status_code == 422
    assert "44 dígitos" in resp.json()["detail"][0]["msg"]


def test_access_key_reject_empty_string(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """Empty string access_key is treated as None (no key)."""
    product = _create_product(client, register_product_for_cleanup)

    purchase = _create_purchase(client, {
        "access_key": "",
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    # Empty string should be normalized to None
    assert purchase["access_key"] is None


# ─── AC: Manual purchases without access_key work ───

def test_purchase_without_access_key(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """A purchase without access_key (manual purchase) works normally."""
    product = _create_product(client, register_product_for_cleanup)

    purchase = _create_purchase(client, {
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    assert purchase["access_key"] is None
    assert len(purchase["items"]) == 1

    # Verify via GET
    get_resp = client.get(f"/api/v1/purchases/{purchase['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["access_key"] is None


# ─── AC: UNIQUE constraint prevents duplicate access_key ───

def test_access_key_unique_constraint(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """Two purchases with the same access_key trigger a database error."""
    product = _create_product(client, register_product_for_cleanup)
    access_key = "99999999999999999999999999999999999999999999"  # 44 digits

    # First purchase succeeds
    purchase1 = _create_purchase(client, {
        "access_key": access_key,
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })
    assert purchase1["access_key"] == access_key

    # Second purchase with same key should fail (IntegrityError → 500 or 409)
    resp = client.post("/api/v1/purchases", json={
        "access_key": access_key,
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    # The endpoint currently returns 503 for IntegrityError (database error)
    # The specific HTTP 409 handling will be added in the OCR confirm endpoint (later step)
    assert resp.status_code in (409, 500, 503)


# ─── AC: NULL access_key values are not unique-conflicted ───

def test_multiple_purchases_without_access_key(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """Multiple purchases without access_key do not conflict (NULL is not unique-checked)."""
    product = _create_product(client, register_product_for_cleanup)

    # Create two purchases without access_key
    purchase1 = _create_purchase(client, {
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })
    purchase2 = _create_purchase(client, {
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "2",
                "commercial_unit_price": "20.00",
            }
        ],
    })

    assert purchase1["id"] != purchase2["id"]
    assert purchase1["access_key"] is None
    assert purchase2["access_key"] is None


# ─── AC: Access key with whitespace is trimmed ───

def test_access_key_trimmed(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    """Access key with leading/trailing whitespace is trimmed before validation."""
    product = _create_product(client, register_product_for_cleanup)
    access_key = "  12345678901234567890123456789012345678901234  "  # 44 digits with spaces

    purchase = _create_purchase(client, {
        "access_key": access_key,
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    })

    # Should be trimmed and stored without spaces
    assert purchase["access_key"] == "12345678901234567890123456789012345678901234"
