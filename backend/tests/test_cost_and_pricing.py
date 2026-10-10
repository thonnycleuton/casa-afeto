from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.products.models import InventoryMovement, Product
from app.baskets.models import Basket, BasketItem, BasketTemplate, BasketTemplateItem


def make_product(client: TestClient, register_cleanup: Any, name: str | None = None, unit: str = "UN") -> dict:
    payload = {"name": name or f"prod-{uuid4().hex[:8]}", "base_unit": unit}
    res = client.post("/api/v1/products", json=payload)
    assert res.status_code == 201
    data = res.json()
    register_cleanup(data["id"])
    return data


def add_entry(client: TestClient, product_id: int, quantity: str, unit_cost: str | None = None) -> dict:
    payload: dict[str, Any] = {"quantity": quantity}
    if unit_cost is not None:
        payload["unit_cost"] = unit_cost
    res = client.post(f"/api/v1/products/{product_id}/inventory/entries", json=payload)
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def register_cleanup() -> Any:
    product_ids: list[int] = []
    template_ids: list[int] = []
    basket_ids: list[int] = []

    def _reg(prod_id: int | None = None, tmpl_id: int | None = None, bsk_id: int | None = None):
        if prod_id: product_ids.append(prod_id)
        if tmpl_id: template_ids.append(tmpl_id)
        if bsk_id: basket_ids.append(bsk_id)

    yield _reg

    with SessionLocal() as db:
        if basket_ids:
            db.query(BasketItem).filter(BasketItem.basket_id.in_(basket_ids)).delete(synchronize_session=False)
            db.query(Basket).filter(Basket.id.in_(basket_ids)).delete(synchronize_session=False)
        if template_ids:
            db.query(BasketTemplateItem).filter(BasketTemplateItem.template_id.in_(template_ids)).delete(synchronize_session=False)
            db.query(BasketTemplate).filter(BasketTemplate.id.in_(template_ids)).delete(synchronize_session=False)
        if product_ids:
            db.query(InventoryMovement).filter(InventoryMovement.product_id.in_(product_ids)).delete(synchronize_session=False)
            db.query(Product).filter(Product.id.in_(product_ids)).delete(synchronize_session=False)
        db.commit()


def test_inventory_entry_unit_cost_validation(client: TestClient, register_cleanup: Any):
    product = make_product(client, register_cleanup)

    # Valid unit cost
    entry1 = add_entry(client, product["id"], "10", "15.50")
    assert entry1["unit_cost"] == "15.50"

    # Entry without unit cost
    entry2 = add_entry(client, product["id"], "5")
    assert entry2["unit_cost"] is None

    # Negative unit cost rejected
    res = client.post(
        f"/api/v1/products/{product['id']}/inventory/entries",
        json={"quantity": "2", "unit_cost": "-5.00"},
    )
    assert res.status_code == 422

    # More than two decimals rejected
    res = client.post(
        f"/api/v1/products/{product['id']}/inventory/entries",
        json={"quantity": "2", "unit_cost": "10.555"},
    )
    assert res.status_code == 422


def test_weighted_average_cost_calculation(client: TestClient, register_cleanup: Any):
    product = make_product(client, register_cleanup)

    # Entry 1: 10 units @ 5.00
    add_entry(client, product["id"], "10", "5.00")
    # Entry 2: 20 units @ 8.00
    add_entry(client, product["id"], "20", "8.00")

    # Product list / get should return weighted average cost = (50 + 160) / 30 = 7.00
    res = client.get("/api/v1/products")
    prods = {p["id"]: p for p in res.json()}
    assert prods[product["id"]]["average_cost"] == "7.00"


def test_weighted_average_cost_ignores_unknown_costs_without_treating_as_zero(client: TestClient, register_cleanup: Any):
    product = make_product(client, register_cleanup)

    # Historical entry without cost: 100 units
    add_entry(client, product["id"], "100")

    # New entry with known cost: 10 units @ 50.00
    add_entry(client, product["id"], "10", "50.00")

    # If unknown cost was treated as 0, avg would be (100*0 + 10*50)/110 = 4.55.
    # But because unknown is ignored from average calculation: avg is 50.00.
    res = client.get("/api/v1/products")
    prods = {p["id"]: p for p in res.json()}
    assert prods[product["id"]]["average_cost"] == "50.00"


def test_product_with_no_known_cost_has_none_average_cost(client: TestClient, register_cleanup: Any):
    product = make_product(client, register_cleanup)
    add_entry(client, product["id"], "10")  # no cost

    res = client.get("/api/v1/products")
    prods = {p["id"]: p for p in res.json()}
    assert prods[product["id"]]["average_cost"] is None


def test_adjustments_do_not_alter_weighted_average_cost(client: TestClient, register_cleanup: Any):
    product = make_product(client, register_cleanup)
    add_entry(client, product["id"], "10", "10.00")

    # Adjustment of +5
    res = client.post(
        f"/api/v1/products/{product['id']}/inventory/adjustments",
        json={"quantity": "5"},
    )
    assert res.status_code == 201
    assert res.json()["unit_cost"] is None

    res = client.get("/api/v1/products")
    prods = {p["id"]: p for p in res.json()}
    assert prods[product["id"]]["average_cost"] == "10.00"


def test_template_estimated_cost_and_suggested_price(client: TestClient, register_cleanup: Any):
    p1 = make_product(client, register_cleanup)
    p2 = make_product(client, register_cleanup)

    add_entry(client, p1["id"], "10", "10.00")  # avg cost = 10.00
    add_entry(client, p2["id"], "10", "20.00")  # avg cost = 20.00

    # Create template with 2 of p1 and 1 of p2
    tmpl_res = client.post(
        "/api/v1/basket-templates",
        json={
            "name": "Template Festa",
            "items": [
                {"product_id": p1["id"], "quantity": "2"},
                {"product_id": p2["id"], "quantity": "1"},
            ],
        },
    )
    assert tmpl_res.status_code == 201
    tmpl = tmpl_res.json()
    register_cleanup(tmpl_id=tmpl["id"])

    # Estimated cost: 2*10.00 + 1*20.00 = 40.00
    # Suggested price: 2 * 40.00 = 80.00
    assert tmpl["has_reliable_cost"] is True
    assert tmpl["estimated_cost"] == "40.00"
    assert tmpl["suggested_price"] == "80.00"
    assert tmpl["price"] is None  # not set yet

    # Check composition item details
    items = {item["product_id"]: item for item in tmpl["items"]}
    assert items[p1["id"]]["unit_cost"] == "10.00"
    assert items[p1["id"]]["total_cost"] == "20.00"
    assert items[p2["id"]]["unit_cost"] == "20.00"
    assert items[p2["id"]]["total_cost"] == "20.00"


def test_template_with_unknown_cost_item_has_no_reliable_suggestion(client: TestClient, register_cleanup: Any):
    p1 = make_product(client, register_cleanup)
    p2 = make_product(client, register_cleanup)

    add_entry(client, p1["id"], "10", "10.00")
    add_entry(client, p2["id"], "10")  # no cost for p2

    tmpl_res = client.post(
        "/api/v1/basket-templates",
        json={
            "name": "Template Incompleto",
            "items": [
                {"product_id": p1["id"], "quantity": "2"},
                {"product_id": p2["id"], "quantity": "1"},
            ],
        },
    )
    assert tmpl_res.status_code == 201
    tmpl = tmpl_res.json()
    register_cleanup(tmpl_id=tmpl["id"])

    assert tmpl["has_reliable_cost"] is False
    assert tmpl["estimated_cost"] is None
    assert tmpl["suggested_price"] is None

    items = {item["product_id"]: item for item in tmpl["items"]}
    assert items[p1["id"]]["unit_cost"] == "10.00"
    assert items[p1["id"]]["total_cost"] == "20.00"
    assert items[p2["id"]]["unit_cost"] is None
    assert items[p2["id"]]["total_cost"] is None


def test_price_preservation_when_costs_change(client: TestClient, register_cleanup: Any):
    p1 = make_product(client, register_cleanup)
    add_entry(client, p1["id"], "10", "10.00")

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

    # Add a much more expensive entry for p1: 10 units @ 30.00
    # New avg cost: (10*10 + 10*30) / 20 = 20.00
    add_entry(client, p1["id"], "10", "30.00")

    # Fetch template again
    get_res = client.get(f"/api/v1/basket-templates/{tmpl['id']}")
    updated_tmpl = get_res.json()

    # Saved price must NOT be overwritten
    assert updated_tmpl["price"] == "35.00"
    # Recalculated estimated cost & suggested price must reflect new costs
    assert updated_tmpl["estimated_cost"] == "20.00"
    assert updated_tmpl["suggested_price"] == "40.00"


def test_basket_estimated_cost_and_suggested_price(client: TestClient, register_cleanup: Any):
    p1 = make_product(client, register_cleanup)
    add_entry(client, p1["id"], "10", "12.00")

    bsk_res = client.post(
        "/api/v1/baskets",
        json={
            "name": "Cesta Avulsa",
            "items": [{"product_id": p1["id"], "quantity": "3"}],
        },
    )
    assert bsk_res.status_code == 201
    bsk = bsk_res.json()
    register_cleanup(bsk_id=bsk["id"])

    assert bsk["has_reliable_cost"] is True
    assert bsk["estimated_cost"] == "36.00"
    assert bsk["suggested_price"] == "72.00"
