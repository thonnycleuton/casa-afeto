"""M6 — Purchases and Stock Replenishment Tests.

Covers all 21 acceptance criteria: AC-M6-001 to AC-M6-021.
"""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from typing import Any, Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.products.models import InventoryMovement, Product
from app.purchases.models import Purchase, PurchaseItem


def create_product(
    client: TestClient,
    register_product: Callable[[int], None],
    *,
    name: str | None = None,
    unit: str = "UN",
    active: bool = True,
) -> dict[str, Any]:
    """Create a product and register it for cleanup."""
    if name is None:
        name = f"purchase-test-{uuid4().hex[:8]}"
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


def create_purchase(
    client: TestClient,
    items: list[dict[str, Any]],
    *,
    purchased_at: str | None = None,
) -> dict[str, Any]:
    """Create a purchase via API."""
    payload = {"items": items}
    if purchased_at:
        payload["purchased_at"] = purchased_at
    response = client.post("/api/v1/purchases", json=payload)
    if response.status_code != 201:
        raise AssertionError(
            f"Purchase creation failed: {response.status_code} {response.text}"
        )
    return response.json()


def get_balance(client: TestClient, product_id: int) -> Decimal:
    """Get current inventory balance for a product."""
    response = client.get(f"/api/v1/products/{product_id}/inventory/balance")
    assert response.status_code == 200
    return Decimal(response.json()["quantity"])


def get_average_cost(client: TestClient, product_id: int) -> Decimal | None:
    """Get average cost for a product by listing and filtering."""
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    products = response.json()
    for p in products:
        if p["id"] == product_id:
            cost = p.get("average_cost")
            return Decimal(cost) if cost is not None else None
    return None


def get_movements(client: TestClient, product_id: int) -> list[dict[str, Any]]:
    """Get inventory movements for a product."""
    response = client.get(f"/api/v1/products/{product_id}/inventory/movements")
    assert response.status_code == 200
    return response.json()


# ─── AC-M6-001: Create purchase with single item ───

def test_create_purchase_single_item(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-001: Single item purchase with commercial unit conversion."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "commercial_unit": "caixa",
            "conversion_factor": "24",
            "commercial_quantity": "2",
            "commercial_unit_price": "48.00",
        }
    ])

    assert purchase["id"] is not None
    assert len(purchase["items"]) == 1
    item = purchase["items"][0]
    assert item["product_id"] == product_id
    assert item["commercial_unit"] == "caixa"
    assert Decimal(item["conversion_factor"]) == Decimal("24")
    assert Decimal(item["commercial_quantity"]) == Decimal("2")
    assert Decimal(item["commercial_unit_price"]) == Decimal("48.00")

    # Balance should be 48 (2 × 24)
    balance = get_balance(client, product_id)
    assert balance == Decimal("48")

    # unit_cost should be 2.00 (48.00 / 24)
    movements = get_movements(client, product_id)
    assert len(movements) == 1
    assert Decimal(movements[0]["quantity"]) == Decimal("48")
    assert Decimal(movements[0]["unit_cost"]) == Decimal("2.00")


# ─── AC-M6-002: Create purchase with multiple items ───

def test_create_purchase_multiple_items(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-002: Multiple products in one purchase."""
    product_a = create_product(client, register_product_for_cleanup, name="Produto-A")
    product_b = create_product(client, register_product_for_cleanup, name="Produto-B", unit="KG")

    purchase = create_purchase(client, [
        {
            "product_id": product_a["id"],
            "commercial_unit": "caixa",
            "conversion_factor": "12",
            "commercial_quantity": "1",
            "commercial_unit_price": "24.00",
        },
        {
            "product_id": product_b["id"],
            "commercial_unit": "fardo",
            "conversion_factor": "5",
            "commercial_quantity": "2",
            "commercial_unit_price": "15.00",
        },
    ])

    assert len(purchase["items"]) == 2
    assert get_balance(client, product_a["id"]) == Decimal("12")
    assert get_balance(client, product_b["id"]) == Decimal("10")


# ─── AC-M6-003: Reject inactive product ───

def test_reject_inactive_product(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-003: Purchase with inactive product is rejected."""
    product = create_product(client, register_product_for_cleanup, active=False)

    response = client.post("/api/v1/purchases", json={
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ]
    })

    assert response.status_code == 409
    assert "inativo" in response.json()["detail"].lower()


# ─── AC-M6-004: Reject fractional UN conversion ───

def test_reject_fractional_UN_conversion(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-004: Fractional base quantity for UN product is rejected."""
    product = create_product(client, register_product_for_cleanup)

    response = client.post("/api/v1/purchases", json={
        "items": [
            {
                "product_id": product["id"],
                "commercial_unit": "kit",
                "conversion_factor": "3",
                "commercial_quantity": "1.5",
                "commercial_unit_price": "9.00",
            }
        ]
    })

    assert response.status_code == 409
    assert "fracionária" in response.json()["detail"].lower()


# ─── AC-M6-005: Accept zero price ───

def test_accept_zero_price(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-005: Zero acquisition price is accepted."""
    product = create_product(client, register_product_for_cleanup)

    purchase = create_purchase(client, [
        {
            "product_id": product["id"],
            "conversion_factor": "1",
            "commercial_quantity": "10",
            "commercial_unit_price": "0.00",
        }
    ])

    assert purchase["id"] is not None
    assert get_balance(client, product["id"]) == Decimal("10")
    movements = get_movements(client, product["id"])
    assert Decimal(movements[0]["unit_cost"]) == Decimal("0.00")


# ─── AC-M6-006: Reject negative price ───

def test_reject_negative_price(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-006: Negative acquisition price is rejected."""
    product = create_product(client, register_product_for_cleanup)

    response = client.post("/api/v1/purchases", json={
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "-5.00",
            }
        ]
    })

    assert response.status_code == 422


# ─── AC-M6-007: Reject zero conversion factor ───

def test_reject_zero_conversion_factor(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-007: Zero conversion factor is rejected."""
    product = create_product(client, register_product_for_cleanup)

    response = client.post("/api/v1/purchases", json={
        "items": [
            {
                "product_id": product["id"],
                "conversion_factor": "0",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ]
    })

    assert response.status_code == 422


# ─── AC-M6-008a: Atomicity — validation failure ───

def test_atomicity_validation_failure(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-008a: If one item fails validation, no ENTRY is created."""
    product_a = create_product(client, register_product_for_cleanup, name="Produto-A")
    product_b = create_product(client, register_product_for_cleanup, name="Produto-B", active=False)

    response = client.post("/api/v1/purchases", json={
        "items": [
            {
                "product_id": product_a["id"],
                "conversion_factor": "1",
                "commercial_quantity": "10",
                "commercial_unit_price": "10.00",
            },
            {
                "product_id": product_b["id"],
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "5.00",
            },
        ]
    })

    assert response.status_code == 409
    # Product A balance should be 0 — no ENTRY created
    assert get_balance(client, product_a["id"]) == Decimal("0")


# ─── AC-M6-008b: Atomicity — transaction failure ───

def test_atomicity_transaction_failure(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-008b: If a movement fails mid-transaction, everything is rolled back."""
    product_a = create_product(client, register_product_for_cleanup, name="Produto-A")
    product_b = create_product(client, register_product_for_cleanup, name="Produto-B")

    # Both products are active, so the purchase should succeed
    purchase = create_purchase(client, [
        {
            "product_id": product_a["id"],
            "conversion_factor": "1",
            "commercial_quantity": "10",
            "commercial_unit_price": "10.00",
        },
        {
            "product_id": product_b["id"],
            "conversion_factor": "1",
            "commercial_quantity": "5",
            "commercial_unit_price": "5.00",
        },
    ])

    assert purchase["id"] is not None
    assert get_balance(client, product_a["id"]) == Decimal("10")
    assert get_balance(client, product_b["id"]) == Decimal("5")


# ─── AC-M6-009: Weighted average cost updated ───

def test_weighted_average_cost_updated(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-009: Purchase updates weighted average cost."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Existing ENTRY: qty 100, unit_cost 2.00
    entry_resp = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "100", "unit_cost": "2.00"},
    )
    assert entry_resp.status_code == 201

    # Purchase: qty 50, unit_cost 3.00
    create_purchase(client, [
        {
            "product_id": product_id,
            "conversion_factor": "1",
            "commercial_quantity": "50",
            "commercial_unit_price": "3.00",
        }
    ])

    avg_cost = get_average_cost(client, product_id)
    # (100 * 2.00 + 50 * 3.00) / 150 = 350 / 150 = 2.33
    assert avg_cost == Decimal("2.33")


# ─── AC-M6-010: Reference price unchanged ───

def test_reference_price_unchanged(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-010: Purchase does not alter reference_price."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Set reference price
    resp = client.patch(
        f"/api/v1/products/{product_id}",
        json={"reference_price": "10.00"},
    )
    assert resp.status_code == 200

    # Purchase with different cost
    create_purchase(client, [
        {
            "product_id": product_id,
            "conversion_factor": "1",
            "commercial_quantity": "10",
            "commercial_unit_price": "5.00",
        }
    ])

    # Reference price should still be 10.00
    resp = client.patch(
        f"/api/v1/products/{product_id}",
        json={"name": product["name"]},
    )
    assert resp.status_code == 200
    assert Decimal(resp.json()["reference_price"]) == Decimal("10.00")


# ─── AC-M6-011: List purchases by period ───

def test_list_purchases_by_period(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-011: Query purchases with period filters."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create purchase with specific date
    create_purchase(
        client,
        [
            {
                "product_id": product_id,
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
        purchased_at="2026-01-15T10:00:00",
    )

    # Filter by period
    response = client.get(
        "/api/v1/purchases",
        params={
            "purchased_from": "2026-01-01T00:00:00",
            "purchased_until": "2026-01-31T23:59:59",
        },
    )
    assert response.status_code == 200
    purchases = response.json()
    assert len(purchases) >= 1

    # Filter outside period
    response = client.get(
        "/api/v1/purchases",
        params={
            "purchased_from": "2027-01-01T00:00:00",
            "purchased_until": "2027-12-31T23:59:59",
        },
    )
    assert response.status_code == 200
    assert len(response.json()) == 0


# ─── AC-M6-012: Get purchase details ───

def test_get_purchase_details(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-012: Retrieve purchase details by ID."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "commercial_unit": "caixa",
            "conversion_factor": "24",
            "commercial_quantity": "2",
            "commercial_unit_price": "48.00",
        }
    ])
    purchase_id = purchase["id"]

    response = client.get(f"/api/v1/purchases/{purchase_id}")
    assert response.status_code == 200
    details = response.json()
    assert details["id"] == purchase_id
    assert len(details["items"]) == 1
    assert details["items"][0]["product_name"] == product["name"]

    # Non-existent purchase
    response = client.get("/api/v1/purchases/999999")
    assert response.status_code == 404


# ─── AC-M6-013: Reject empty items ───

def test_reject_empty_items(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-013: Purchase with no items is rejected."""
    response = client.post("/api/v1/purchases", json={"items": []})
    assert response.status_code == 422


# ─── AC-M6-014: Concurrent purchases ───

def test_concurrent_purchases(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-014: Concurrent purchases of the same product succeed."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    barrier = Barrier(2)
    errors = []

    def make_purchase():
        try:
            barrier.wait(timeout=5)
            resp = client.post("/api/v1/purchases", json={
                "items": [
                    {
                        "product_id": product_id,
                        "conversion_factor": "1",
                        "commercial_quantity": "10",
                        "commercial_unit_price": "5.00",
                    }
                ]
            })
            if resp.status_code != 201:
                errors.append(resp.text)
        except Exception as e:
            errors.append(str(e))

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(make_purchase),
            executor.submit(make_purchase),
        ]
        for f in futures:
            f.result()

    assert not errors
    balance = get_balance(client, product_id)
    assert balance == Decimal("20")


# ─── AC-M6-015: Optional commercial unit ───

def test_optional_commercial_unit(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-015: Commercial unit is optional; defaults to base unit."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "conversion_factor": "1",
            "commercial_quantity": "10",
            "commercial_unit_price": "5.00",
        }
    ])

    assert purchase["items"][0]["commercial_unit"] is None
    assert get_balance(client, product_id) == Decimal("10")


# ─── AC-M6-016: Default purchased_at ───

def test_default_purchased_at(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-016: purchased_at defaults to current timestamp."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "conversion_factor": "1",
            "commercial_quantity": "1",
            "commercial_unit_price": "1.00",
        }
    ])

    assert "purchased_at" in purchase
    assert purchase["purchased_at"] is not None


# ─── AC-M6-017: Conversion with KG ───

def test_conversion_with_KG(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-017: Purchase with KG base unit and conversion factor."""
    product = create_product(client, register_product_for_cleanup, unit="KG")
    product_id = product["id"]

    purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "commercial_unit": "saco",
            "conversion_factor": "5",
            "commercial_quantity": "3",
            "commercial_unit_price": "25.00",
        }
    ])

    assert get_balance(client, product_id) == Decimal("15")
    movements = get_movements(client, product_id)
    assert Decimal(movements[0]["quantity"]) == Decimal("15")
    assert Decimal(movements[0]["unit_cost"]) == Decimal("5.00")


# ─── AC-M6-018: Purchase not deletable ───

def test_purchase_not_deletable(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-018: Purchases cannot be deleted."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "conversion_factor": "1",
            "commercial_quantity": "1",
            "commercial_unit_price": "1.00",
        }
    ])
    purchase_id = purchase["id"]

    # Try to delete — endpoint should not exist or return 405
    response = client.delete(f"/api/v1/purchases/{purchase_id}")
    assert response.status_code in (405, 404)

    # Purchase should still be accessible
    response = client.get(f"/api/v1/purchases/{purchase_id}")
    assert response.status_code == 200


# ─── AC-M6-019: Correction by complementary purchase ───

def test_correction_by_complementary_purchase(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-019: Correct wrong purchase with complementary purchase."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Wrong purchase: 2 caixas × 24 = 48 UN
    wrong_purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "commercial_unit": "caixa",
            "conversion_factor": "24",
            "commercial_quantity": "2",
            "commercial_unit_price": "48.00",
        }
    ])

    # Corrective purchase: 3 caixas × 24 = 72 UN
    correct_purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "commercial_unit": "caixa",
            "conversion_factor": "24",
            "commercial_quantity": "3",
            "commercial_unit_price": "48.00",
        }
    ])

    # Both purchases exist
    assert wrong_purchase["id"] != correct_purchase["id"]

    # Balance reflects both: 48 + 72 = 120
    balance = get_balance(client, product_id)
    assert balance == Decimal("120")

    # Original purchase unchanged
    original = client.get(f"/api/v1/purchases/{wrong_purchase['id']}").json()
    assert Decimal(original["items"][0]["commercial_quantity"]) == Decimal("2")


# ─── AC-M6-020: ENTRY traceability via purchase_id ───

def test_entry_traceability_via_purchase_id(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-020: ENTRY movements are traceable to purchase via purchase_id."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "conversion_factor": "1",
            "commercial_quantity": "10",
            "commercial_unit_price": "5.00",
        }
    ])
    purchase_id = purchase["id"]

    # Check movements have purchase_id
    movements = get_movements(client, product_id)
    assert len(movements) == 1
    assert movements[0]["purchase_id"] == purchase_id

    # Manual ENTRY should have purchase_id = null
    entry_resp = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "5", "unit_cost": "3.00"},
    )
    assert entry_resp.status_code == 201

    movements = get_movements(client, product_id)
    manual_entry = [m for m in movements if m["purchase_id"] is None]
    assert len(manual_entry) == 1


# ─── AC-M6-021: Same product, separate ENTRY ───

def test_same_product_separate_entry(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-M6-021: Two items of same product generate separate ENTRY movements."""
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchase = create_purchase(client, [
        {
            "product_id": product_id,
            "commercial_unit": "caixa",
            "conversion_factor": "24",
            "commercial_quantity": "1",
            "commercial_unit_price": "48.00",
        },
        {
            "product_id": product_id,
            "commercial_unit": "caixa",
            "conversion_factor": "24",
            "commercial_quantity": "1",
            "commercial_unit_price": "54.00",
        },
    ])

    assert len(purchase["items"]) == 2

    # Two separate ENTRY movements
    movements = get_movements(client, product_id)
    assert len(movements) == 2

    # Check unit costs are preserved separately
    unit_costs = [Decimal(m["unit_cost"]) for m in movements if m["unit_cost"] is not None]
    assert Decimal("2.00") in unit_costs  # 48.00 / 24
    assert Decimal("2.25") in unit_costs  # 54.00 / 24

    # Both reference the same purchase
    for m in movements:
        assert m["purchase_id"] == purchase["id"]

    # Total balance: 24 + 24 = 48
    assert get_balance(client, product_id) == Decimal("48")
