"""M13 Step 4 — Discount Persistence Tests.

Covers acceptance criteria for discount persistence:
- Create DRAFT with item discounts
- Create DRAFT with document discounts
- Create DRAFT without discounts (NULL/empty)
- Update DRAFT item discounts
- Update DRAFT document discounts
- Update DRAFT preserves document discounts when omitted
- Confirm preserves discounts
- CONFIRMED rejects item discount change (409)
- CONFIRMED rejects document discount change (409)
- Read purchase with discounts
"""
from decimal import Decimal
from typing import Any, Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.products.models import InventoryMovement, Product
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
        name = f"discount-test-{uuid4().hex[:8]}"
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


# ─── Test 1: Create DRAFT with item discounts ───


def test_create_draft_with_item_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Create a DRAFT with item discounts; verify persistence."""
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
                "item_discounts": [
                    {"value": "5.00", "nature": "volume", "description": "Desconto por volume"},
                    {"value": "2.50", "nature": "promocional", "description": "Promoção"},
                ],
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    assert data["status"] == "DRAFT"
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["item_discounts"] is not None
    assert len(item["item_discounts"]) == 2
    assert Decimal(item["item_discounts"][0]["value"]) == Decimal("5.00")
    assert item["item_discounts"][0]["nature"] == "volume"
    assert item["item_discounts"][1]["nature"] == "promocional"


# ─── Test 2: Create DRAFT with document discounts ───


def test_create_draft_with_document_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Create a DRAFT with document discounts; verify table persistence."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "3",
                "commercial_unit_price": "20.00",
            }
        ],
        "document_discounts": [
            {"value": "10.00", "nature": "frete", "description": "Desconto de frete"},
            {"value": "5.00", "nature": "cashback", "description": "Cashback fornecedor"},
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    assert len(data["document_discounts"]) == 2
    assert Decimal(data["document_discounts"][0]["value"]) == Decimal("10.00")
    assert data["document_discounts"][0]["nature"] == "frete"
    assert Decimal(data["document_discounts"][1]["value"]) == Decimal("5.00")


# ─── Test 3: Create DRAFT without discounts ───


def test_create_draft_without_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Create a DRAFT without discounts; verify NULL/empty."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "2",
                "commercial_unit_price": "15.00",
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    assert data["items"][0]["item_discounts"] is None
    assert data["document_discounts"] == []


# ─── Test 4: Update DRAFT item discounts ───


def test_update_draft_item_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Edit a DRAFT: change item discounts."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create DRAFT with discounts
    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
                "item_discounts": [
                    {"value": "3.00", "nature": "antigo", "description": "Desconto antigo"},
                ],
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Update with new discounts
    update_payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
                "item_discounts": [
                    {"value": "7.00", "nature": "novo", "description": "Desconto novo"},
                ],
            }
        ]
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data["items"][0]["item_discounts"]) == 1
    assert Decimal(data["items"][0]["item_discounts"][0]["value"]) == Decimal("7.00")
    assert data["items"][0]["item_discounts"][0]["nature"] == "novo"


# ─── Test 5: Update DRAFT document discounts ───


def test_update_draft_document_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Edit a DRAFT: replace document discounts."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create DRAFT with document discounts
    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "2",
                "commercial_unit_price": "10.00",
            }
        ],
        "document_discounts": [
            {"value": "5.00", "nature": "antigo", "description": "Desconto antigo"},
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Update document discounts
    update_payload = {
        "document_discounts": [
            {"value": "15.00", "nature": "novo", "description": "Desconto novo"},
        ]
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert len(data["document_discounts"]) == 1
    assert Decimal(data["document_discounts"][0]["value"]) == Decimal("15.00")
    assert data["document_discounts"][0]["nature"] == "novo"


# ─── Test 6: Update DRAFT preserves document discounts when omitted ───


def test_update_draft_preserves_document_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Edit a DRAFT without sending document_discounts; preserve existing."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create DRAFT with document discounts
    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "2",
                "commercial_unit_price": "10.00",
            }
        ],
        "document_discounts": [
            {"value": "8.00", "nature": "frete", "description": "Desconto de frete"},
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Update only supplier_name — no document_discounts in payload
    update_payload = {"supplier_name": "Fornecedor Atualizado"}
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["supplier_name"] == "Fornecedor Atualizado"
    assert len(data["document_discounts"]) == 1
    assert Decimal(data["document_discounts"][0]["value"]) == Decimal("8.00")


# ─── Test 7: Confirm preserves discounts ───


def test_confirm_preserves_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Confirm a DRAFT with discounts; discounts must be preserved."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create DRAFT with both item and document discounts
    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
                "item_discounts": [
                    {"value": "3.00", "nature": "volume", "description": "Desconto por volume"},
                ],
            }
        ],
        "document_discounts": [
            {"value": "10.00", "nature": "frete", "description": "Desconto de frete"},
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # Confirm
    response = client.post(f"/api/v1/purchases/{purchase_id}/confirm")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["status"] == "CONFIRMED"

    # Item discounts preserved
    assert data["items"][0]["item_discounts"] is not None
    assert len(data["items"][0]["item_discounts"]) == 1
    assert Decimal(data["items"][0]["item_discounts"][0]["value"]) == Decimal("3.00")

    # Document discounts preserved
    assert len(data["document_discounts"]) == 1
    assert Decimal(data["document_discounts"][0]["value"]) == Decimal("10.00")


# ─── Test 8: CONFIRMED rejects item discount change (409) ───


def test_confirmed_reject_item_discounts_change(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Try to change items (with discounts) of a CONFIRMED purchase; 409."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create a confirmed purchase directly
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
    purchase_id = response.json()["id"]

    # Try to update items (which would include discounts)
    update_payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
                "item_discounts": [
                    {"value": "5.00", "nature": "tentativa", "description": "Tentativa"},
                ],
            }
        ]
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 409, response.text


# ─── Test 9: CONFIRMED rejects document discount change (409) ───


def test_confirmed_reject_document_discounts_change(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """Try to change document discounts of a CONFIRMED purchase; 409."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create a confirmed purchase directly
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
    purchase_id = response.json()["id"]

    # Try to update document discounts
    update_payload = {
        "document_discounts": [
            {"value": "99.00", "nature": "tentativa", "description": "Tentativa"},
        ]
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 409, response.text


# ─── Test 10: Read purchase with discounts ───


def test_read_purchase_with_discounts(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """GET a purchase with discounts; verify complete response."""
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create DRAFT with all discount types
    payload = {
        "supplier_name": "Fornecedor Teste",
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "3",
                "commercial_unit_price": "20.00",
                "item_discounts": [
                    {"value": "4.00", "nature": "volume", "description": "Desconto por volume"},
                ],
            }
        ],
        "document_discounts": [
            {"value": "12.00", "nature": "frete", "description": "Desconto de frete"},
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    purchase_id = response.json()["id"]

    # GET the purchase
    response = client.get(f"/api/v1/purchases/{purchase_id}")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["supplier_name"] == "Fornecedor Teste"
    assert len(data["items"]) == 1
    assert data["items"][0]["item_discounts"] is not None
    assert len(data["items"][0]["item_discounts"]) == 1
    assert Decimal(data["items"][0]["item_discounts"][0]["value"]) == Decimal("4.00")
    assert len(data["document_discounts"]) == 1
    assert Decimal(data["document_discounts"][0]["value"]) == Decimal("12.00")
    assert data["document_discounts"][0]["nature"] == "frete"
