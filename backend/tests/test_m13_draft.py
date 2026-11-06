"""M13 Step 2 — Draft Purchase Service Tests.

Covers acceptance criteria:
- AC-DRAFT-001: Create draft with items and fiscal data
- AC-DRAFT-002: Draft does not generate ENTRY
- AC-DRAFT-003: Reject inactive product in draft
- AC-DRAFT-004: Reject fractional UN conversion in draft
- AC-DRAFT-008: Edit draft — change items and data
- AC-DRAFT-009: Preserve document_path on edit
- AC-DRAFT-019: Edit confirmed purchase — fiscal data only
- AC-DRAFT-021: Reject item changes on confirmed purchase (409)
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
        name = f"draft-test-{uuid4().hex[:8]}"
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


def _get_balance(client: TestClient, product_id: int) -> Decimal:
    """Get current inventory balance for a product."""
    response = client.get(f"/api/v1/products/{product_id}/inventory/balance")
    assert response.status_code == 200
    return Decimal(response.json()["quantity"])


def _get_movements(client: TestClient, product_id: int) -> list[dict[str, Any]]:
    """Get inventory movements for a product."""
    response = client.get(f"/api/v1/products/{product_id}/inventory/movements")
    assert response.status_code == 200
    return response.json()


# ─── AC-DRAFT-001: Create draft with items and fiscal data ───


def test_create_draft_with_items(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-DRAFT-001: Create a draft purchase with items and optional fiscal data.
    
    Expected: 201 with status DRAFT, items present, fiscal data preserved.
    """
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    payload = {
        "purchased_at": "2025-01-15T10:00:00",
        "supplier_name": "Fornecedor Teste",
        "cnpj": "12.345.678/0001-99",
        "invoice_number": "NF-001",
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "caixa",
                "conversion_factor": "24",
                "commercial_quantity": "2",
                "commercial_unit_price": "48.00",
            }
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    assert data["status"] == "DRAFT"
    assert data["supplier_name"] == "Fornecedor Teste"
    assert data["cnpj"] == "12.345.678/0001-99"
    assert data["invoice_number"] == "NF-001"
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_id"] == product_id
    assert item["commercial_unit"] == "caixa"
    assert Decimal(item["conversion_factor"]) == Decimal("24")
    assert Decimal(item["commercial_quantity"]) == Decimal("2")
    assert Decimal(item["commercial_unit_price"]) == Decimal("48.00")


# ─── AC-DRAFT-002: Draft does not generate ENTRY ───


def test_draft_no_entry_generated(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-DRAFT-002: Creating a draft must NOT generate inventory ENTRY movements.
    
    Expected: balance=0, movements=0 for the product.
    """
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "caixa",
                "conversion_factor": "24",
                "commercial_quantity": "2",
                "commercial_unit_price": "48.00",
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text

    # Balance should remain 0 — no ENTRY generated
    balance = _get_balance(client, product_id)
    assert balance == Decimal("0"), f"Expected balance 0, got {balance}"

    # No movements should exist
    movements = _get_movements(client, product_id)
    assert len(movements) == 0, f"Expected 0 movements, got {len(movements)}"


# ─── AC-DRAFT-003: Reject inactive product in draft ───


def test_draft_reject_inactive_product(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-DRAFT-003: Creating a draft with an inactive product must return 409.
    
    Expected: HTTP 409 with business rule error message.
    """
    product = _create_product(
        client, register_product_for_cleanup, active=False
    )
    product_id = product["id"]

    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 409, response.text


# ─── AC-DRAFT-004: Reject fractional UN conversion in draft ───


def test_draft_reject_fractional_UN(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-DRAFT-004: Creating a draft with fractional UN conversion must return 409.
    
    Expected: HTTP 409 with business rule error about fractional quantity.
    """
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # 3 * 0.5 = 1.5 (fractional for UN)
    payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "meio",
                "conversion_factor": "0.5",
                "commercial_quantity": "3",
                "commercial_unit_price": "10.00",
            }
        ]
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 409, response.text


# ─── AC-DRAFT-008: Edit draft — change items and data ───


def test_update_draft_full_edit(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-DRAFT-008: Edit a DRAFT purchase — change items, quantities, prices and data.
    
    Expected: 200 with updated items and data.
    """
    product1 = _create_product(client, register_product_for_cleanup)
    product2 = _create_product(client, register_product_for_cleanup)

    # Create draft with one item
    payload = {
        "supplier_name": "Original",
        "items": [
            {
                "product_id": product1["id"],
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    draft = response.json()
    purchase_id = draft["id"]

    # Update draft: change supplier, replace items
    update_payload = {
        "supplier_name": "Atualizado",
        "items": [
            {
                "product_id": product2["id"],
                "commercial_unit": "caixa",
                "conversion_factor": "12",
                "commercial_quantity": "3",
                "commercial_unit_price": "25.00",
            }
        ],
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 200, response.text

    updated = response.json()
    assert updated["status"] == "DRAFT"
    assert updated["supplier_name"] == "Atualizado"
    assert len(updated["items"]) == 1
    item = updated["items"][0]
    assert item["product_id"] == product2["id"]
    assert item["commercial_unit"] == "caixa"
    assert Decimal(item["conversion_factor"]) == Decimal("12")
    assert Decimal(item["commercial_quantity"]) == Decimal("3")
    assert Decimal(item["commercial_unit_price"]) == Decimal("25.00")


# ─── AC-DRAFT-009: Preserve document_path on edit ───


def test_update_draft_preserves_document_path(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-DRAFT-009: Editing a draft without sending document_path should preserve it.
    
    Expected: document_path remains unchanged after PATCH.
    """
    product = _create_product(client, register_product_for_cleanup)

    # Create draft with document_path
    payload = {
        "document_path": "/uploads/nf-001.pdf",
        "items": [
            {
                "product_id": product["id"],
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "10.00",
            }
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    draft = response.json()
    purchase_id = draft["id"]
    assert draft["document_path"] == "/uploads/nf-001.pdf"

    # Update without document_path — should preserve
    update_payload = {
        "supplier_name": "Novo Fornecedor",
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 200, response.text

    updated = response.json()
    assert updated["document_path"] == "/uploads/nf-001.pdf"
    assert updated["supplier_name"] == "Novo Fornecedor"


# ─── AC-DRAFT-019: Edit confirmed purchase — fiscal data only ───


def test_update_confirmed_fiscal_only(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-DRAFT-019: Edit a CONFIRMED purchase — only fiscal/descriptive data allowed.
    
    Expected: 200 with updated fiscal data, items unchanged.
    """
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create a confirmed purchase via POST /purchases
    purchase_payload = {
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
    response = client.post("/api/v1/purchases", json=purchase_payload)
    assert response.status_code == 201, response.text
    purchase = response.json()
    purchase_id = purchase["id"]
    assert purchase["status"] == "CONFIRMED"
    original_items = purchase["items"]

    # Update fiscal data only
    update_payload = {
        "supplier_name": "Fornecedor Atualizado",
        "cnpj": "98.765.432/0001-00",
        "invoice_number": "NF-999",
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 200, response.text

    updated = response.json()
    assert updated["supplier_name"] == "Fornecedor Atualizado"
    assert updated["cnpj"] == "98.765.432/0001-00"
    assert updated["invoice_number"] == "NF-999"
    # Items should be unchanged
    assert len(updated["items"]) == len(original_items)
    assert updated["items"][0]["id"] == original_items[0]["id"]


# ─── AC-DRAFT-021: Reject item changes on confirmed purchase ───


def test_update_confirmed_reject_items(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """AC-DRAFT-021: Attempting to change items on a CONFIRMED purchase must return 409.
    
    Expected: HTTP 409 with business rule error.
    """
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    # Create a confirmed purchase
    purchase_payload = {
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
    response = client.post("/api/v1/purchases", json=purchase_payload)
    assert response.status_code == 201, response.text
    purchase = response.json()
    purchase_id = purchase["id"]

    # Try to update items — should be rejected
    update_payload = {
        "items": [
            {
                "product_id": product_id,
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "10",
                "commercial_unit_price": "10.00",
            }
        ]
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 409, response.text


# ─── Additional edge cases ───


def test_update_confirmed_reject_empty_items(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """CONFIRMED purchase with explicit items: [] should also return 409.
    
    Even an empty list sent explicitly is considered an items modification.
    """
    product = _create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    purchase_payload = {
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
    response = client.post("/api/v1/purchases", json=purchase_payload)
    assert response.status_code == 201, response.text
    purchase = response.json()
    purchase_id = purchase["id"]

    # Send explicit empty items list
    update_payload = {"items": []}
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 409, response.text


def test_update_draft_clear_items_with_empty_list(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """DRAFT purchase with explicit items: [] should clear all items.
    
    Empty list sent explicitly removes all items from a DRAFT.
    """
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
    draft = response.json()
    purchase_id = draft["id"]
    assert len(draft["items"]) == 1

    # Clear items with explicit empty list
    update_payload = {"items": []}
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 200, response.text

    updated = response.json()
    assert len(updated["items"]) == 0


def test_update_nonexistent_purchase_returns_404(
    client: TestClient,
) -> None:
    """PATCH on a nonexistent purchase should return 404."""
    update_payload = {"supplier_name": "Teste"}
    response = client.patch("/api/v1/purchases/99999", json=update_payload)
    assert response.status_code == 404, response.text


def test_create_draft_empty_items_allowed(
    client: TestClient,
) -> None:
    """Creating a draft with no items (empty list) should be allowed."""
    payload = {
        "supplier_name": "Fornecedor",
        "items": [],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    assert data["status"] == "DRAFT"
    assert data["supplier_name"] == "Fornecedor"
    assert len(data["items"]) == 0


def test_update_draft_validates_items_before_replace(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    """When updating a DRAFT with invalid items, existing items should be preserved.
    
    If validation fails on new items, the transaction rolls back and original items remain.
    """
    product_active = _create_product(client, register_product_for_cleanup)
    product_inactive = _create_product(
        client, register_product_for_cleanup, active=False
    )

    # Create draft with valid item
    payload = {
        "items": [
            {
                "product_id": product_active["id"],
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "5",
                "commercial_unit_price": "10.00",
            }
        ],
    }
    response = client.post("/api/v1/purchases/draft", json=payload)
    assert response.status_code == 201, response.text
    draft = response.json()
    purchase_id = draft["id"]
    assert len(draft["items"]) == 1

    # Try to update with an inactive product — should fail with 409
    update_payload = {
        "items": [
            {
                "product_id": product_inactive["id"],
                "commercial_unit": "UN",
                "conversion_factor": "1",
                "commercial_quantity": "1",
                "commercial_unit_price": "5.00",
            }
        ]
    }
    response = client.patch(f"/api/v1/purchases/{purchase_id}", json=update_payload)
    assert response.status_code == 409, response.text

    # Original items should still be intact (transaction rollback)
    response = client.get(f"/api/v1/purchases/{purchase_id}")
    assert response.status_code == 200, response.text
    recovered = response.json()
    assert len(recovered["items"]) == 1
    assert recovered["items"][0]["product_id"] == product_active["id"]
