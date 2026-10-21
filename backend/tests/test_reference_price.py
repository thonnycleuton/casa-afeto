"""Tests for reference_price refactoring — M1 products and M2 basket pricing."""
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.products.models import InventoryMovement, Product
from app.baskets.models import BasketTemplate, BasketTemplateItem
from app.sales.models import Sale, SaleBasket, SaleBasketItem
from app.inventory.models import StockBatch


def make_product(client: TestClient, register_cleanup: Any, name: str | None = None, unit: str = "UN", reference_price: str | None = None) -> dict:
    payload: dict[str, Any] = {"name": name or f"prod-{uuid4().hex[:8]}", "base_unit": unit}
    if reference_price is not None:
        payload["reference_price"] = reference_price
    res = client.post("/api/v1/products", json=payload)
    assert res.status_code == 201, f"Failed to create product: {res.text}"
    data = res.json()
    register_cleanup(data["id"])
    return data


def add_entry(client: TestClient, product_id: int, quantity: str, unit_cost: str | None = None) -> dict:
    payload: dict[str, Any] = {"quantity": quantity}
    if unit_cost is not None:
        payload["unit_cost"] = unit_cost
    res = client.post(f"/api/v1/products/{product_id}/inventory/entries", json=payload)
    assert res.status_code == 201, f"Failed to add entry: {res.text}"
    return res.json()


@pytest.fixture
def register_cleanup() -> Any:
    product_ids: list[int] = []
    template_ids: list[int] = []
    basket_ids: list[int] = []
    sale_ids: list[int] = []

    def _reg(prod_id: int | None = None, tmpl_id: int | None = None, bsk_id: int | None = None, sale_id: int | None = None):
        if prod_id:
            product_ids.append(prod_id)
        if tmpl_id:
            template_ids.append(tmpl_id)
        if bsk_id:
            basket_ids.append(bsk_id)
        if sale_id:
            sale_ids.append(sale_id)

    yield _reg

    with SessionLocal() as db:
        if sale_ids:
            db.query(SaleBasketItem).filter(SaleBasketItem.sale_basket_id.in_(
                db.query(SaleBasket.id).filter(SaleBasket.sale_id.in_(sale_ids)).subquery()
            )).delete(synchronize_session=False)
            db.query(SaleBasket).filter(SaleBasket.sale_id.in_(sale_ids)).delete(synchronize_session=False)
            db.query(Sale).filter(Sale.id.in_(sale_ids)).delete(synchronize_session=False)
        if basket_ids:
            db.query(BasketItem).filter(BasketItem.basket_id.in_(basket_ids)).delete(synchronize_session=False)
            db.query(Basket).filter(Basket.id.in_(basket_ids)).delete(synchronize_session=False)
        if template_ids:
            db.query(BasketTemplateItem).filter(BasketTemplateItem.template_id.in_(template_ids)).delete(synchronize_session=False)
            db.query(BasketTemplate).filter(BasketTemplate.id.in_(template_ids)).delete(synchronize_session=False)
        if product_ids:
            db.query(StockBatch).filter(StockBatch.product_id.in_(product_ids)).delete(synchronize_session=False)
            db.query(InventoryMovement).filter(InventoryMovement.product_id.in_(product_ids)).delete(synchronize_session=False)
            db.query(Product).filter(Product.id.in_(product_ids)).delete(synchronize_session=False)
        db.commit()


# =============================================================================
# M1 — Product reference_price tests (AC-41 to AC-45)
# =============================================================================


def test_create_product_with_reference_price(client: TestClient, register_cleanup: Any):
    """AC-41: Create product with valid reference_price."""
    product = make_product(client, register_cleanup, reference_price="12.50")
    assert product["reference_price"] == "12.50"


def test_create_product_without_reference_price(client: TestClient, register_cleanup: Any):
    """AC-42: Create product without reference_price -> null."""
    product = make_product(client, register_cleanup)
    assert product["reference_price"] is None


def test_update_product_reference_price(client: TestClient, register_cleanup: Any):
    """AC-43: Edit reference_price on existing product."""
    product = make_product(client, register_cleanup)
    assert product["reference_price"] is None

    res = client.patch(f"/api/v1/products/{product['id']}", json={"reference_price": "25.00"})
    assert res.status_code == 200, f"Failed to update: {res.text}"
    updated = res.json()
    assert updated["reference_price"] == "25.00"


def test_update_product_clear_reference_price(client: TestClient, register_cleanup: Any):
    """Set reference_price to null via PATCH."""
    product = make_product(client, register_cleanup, reference_price="10.00")
    assert product["reference_price"] == "10.00"

    res = client.patch(f"/api/v1/products/{product['id']}", json={"reference_price": None})
    assert res.status_code == 200, f"Failed to clear: {res.text}"
    updated = res.json()
    assert updated["reference_price"] is None


def test_reject_negative_reference_price(client: TestClient, register_cleanup: Any):
    """AC-44: Reject negative reference_price."""
    res = client.post("/api/v1/products", json={
        "name": f"neg-{uuid4().hex[:8]}",
        "base_unit": "UN",
        "reference_price": "-5.00",
    })
    assert res.status_code == 422


def test_reject_reference_price_more_than_two_decimals(client: TestClient, register_cleanup: Any):
    """AC-45: Reject reference_price with >2 decimal places."""
    res = client.post("/api/v1/products", json={
        "name": f"dec-{uuid4().hex[:8]}",
        "base_unit": "UN",
        "reference_price": "10.555",
    })
    assert res.status_code == 422


def test_reference_price_zero_is_allowed(client: TestClient, register_cleanup: Any):
    """Zero (0.00) is valid and distinct from null."""
    product = make_product(client, register_cleanup, reference_price="0.00")
    assert product["reference_price"] == "0.00"


def test_reference_price_not_affected_by_inventory_entry(client: TestClient, register_cleanup: Any):
    """Reference price does not change when inventory entry is recorded."""
    product = make_product(client, register_cleanup, reference_price="10.00")
    add_entry(client, product["id"], "10", "15.00")

    res = client.get("/api/v1/products")
    assert res.status_code == 200
    products = {p["id"]: p for p in res.json()}
    assert products[product["id"]]["reference_price"] == "10.00"


def test_template_reference_cost_calculation(client: TestClient, register_cleanup: Any):
    """Template reference cost uses reference_price."""
    p1 = make_product(client, register_cleanup, reference_price="10.00")
    p2 = make_product(client, register_cleanup, reference_price="20.00")

    tmpl_res = client.post(
        "/api/v1/basket-templates",
        json={
            "name": "Template Teste",
            "items": [
                {"product_id": p1["id"], "quantity": "2"},
                {"product_id": p2["id"], "quantity": "1"},
            ],
        },
    )
    assert tmpl_res.status_code == 201
    tmpl = tmpl_res.json()
    register_cleanup(tmpl_id=tmpl["id"])

    assert tmpl["has_reliable_cost"] is True
    assert tmpl["estimated_cost"] == "40.00"
    assert tmpl["suggested_price"] == "80.00"


def test_template_price_preserved_on_reference_price_change(client: TestClient, register_cleanup: Any):
    """Saved template price is NOT overwritten when reference_price changes."""
    p1 = make_product(client, register_cleanup, reference_price="10.00")

    tmpl_res = client.post(
        "/api/v1/basket-templates",
        json={
            "name": "Template Preço Fixo",
            "price": "35.00",
            "items": [{"product_id": p1["id"], "quantity": "1"}],
        },
    )
    assert tmpl_res.status_code == 201
    tmpl = tmpl_res.json()
    register_cleanup(tmpl_id=tmpl["id"])

    assert tmpl["price"] == "35.00"
    assert tmpl["estimated_cost"] == "10.00"
    assert tmpl["suggested_price"] == "20.00"

    # Change reference_price
    client.patch(f"/api/v1/products/{p1['id']}", json={"reference_price": "30.00"})

    # Fetch template again
    get_res = client.get(f"/api/v1/basket-templates/{tmpl['id']}")
    updated_tmpl = get_res.json()

    # Saved price must NOT be overwritten
    assert updated_tmpl["price"] == "35.00"
    # Recalculated values must reflect new reference_price
    assert updated_tmpl["estimated_cost"] == "30.00"
    assert updated_tmpl["suggested_price"] == "60.00"


# =============================================================================
# M4 — Sale snapshot regression
# =============================================================================


def test_sale_snapshot_preserved_after_reference_price_change(
    client: TestClient, register_cleanup: Any
):
    """Sale basket prices are not recalculated when reference_price changes."""
    from app.customers.models import Customer

    p1 = make_product(client, register_cleanup, reference_price="10.00")

    # Create a customer
    cust_res = client.post("/api/v1/customers", json={
        "name": f"Cliente {uuid4().hex[:8]}",
        "phone": "11999999999",
    })
    assert cust_res.status_code == 201
    customer = cust_res.json()

    # Create a template
    tmpl_res = client.post(
        "/api/v1/basket-templates",
        json={
            "name": "Template Venda",
            "price": "25.00",
            "items": [{"product_id": p1["id"], "quantity": "1"}],
        },
    )
    assert tmpl_res.status_code == 201
    tmpl = tmpl_res.json()
    register_cleanup(tmpl_id=tmpl["id"])

    # Create a sale with the template
    sale_res = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [
                {
                    "template_id": tmpl["id"],
                    "price": "25.00",
                }
            ],
        },
    )
    assert sale_res.status_code == 201, f"Failed to create sale: {sale_res.text}"
    sale = sale_res.json()
    register_cleanup(sale_id=sale["id"])

    # Change reference_price
    client.patch(f"/api/v1/products/{p1['id']}", json={"reference_price": "50.00"})

    # Fetch sale again
    get_res = client.get(f"/api/v1/sales/{sale['id']}")
    updated_sale = get_res.json()

    # Sale basket price must remain unchanged
    assert updated_sale["baskets"][0]["price"] == "25.00"
    assert updated_sale["total"] == "25.00"
