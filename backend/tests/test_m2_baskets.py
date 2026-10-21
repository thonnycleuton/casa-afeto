from collections.abc import Callable, Iterator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.baskets.models import BasketTemplate, BasketTemplateItem
from app.core.database import SessionLocal
from app.products.models import InventoryMovement, Product
from app.inventory.models import StockBatch


@pytest.fixture
def register_m2_cleanup() -> Iterator[Callable[[str, int], None]]:
    registered: dict[str, list[int]] = {
        "product": [],
        "template": [],
    }

    def register(kind: str, identifier: int) -> None:
        registered[kind].append(identifier)

    yield register
    with SessionLocal() as db:
        db.query(BasketTemplateItem).filter(
            BasketTemplateItem.template_id.in_(registered["template"])
        ).delete(synchronize_session=False)
        db.query(BasketTemplate).filter(
            BasketTemplate.id.in_(registered["template"])
        ).delete(synchronize_session=False)
        db.query(StockBatch).filter(
            StockBatch.product_id.in_(registered["product"])
        ).delete(synchronize_session=False)
        db.query(InventoryMovement).filter(
            InventoryMovement.product_id.in_(registered["product"])
        ).delete(synchronize_session=False)
        db.query(Product).filter(Product.id.in_(registered["product"])).delete(
            synchronize_session=False
        )
        db.commit()


def make_product(
    client: TestClient,
    register: Callable[[str, int], None],
    name: str,
    unit: str = "UN",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/products", json={"name": name, "base_unit": unit}
    )
    assert response.status_code == 201, response.text
    product = response.json()
    register("product", product["id"])
    return product


def make_template(
    client: TestClient,
    register: Callable[[str, int], None],
    name: str,
    items: list[dict[str, Any]] | None = None,
    price: Any = ...,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name, "items": items or []}
    if price is not ...:
        payload["price"] = price
    response = client.post(
        "/api/v1/basket-templates",
        json=payload,
    )
    assert response.status_code == 201, response.text
    template = response.json()
    register("template", template["id"])
    return template


def test_template_empty_active_lifecycle(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    template = make_template(client, register_m2_cleanup, "Template vazio")
    template_id = template["id"]
    assert template["active"] is True
    assert template["items"] == []
    assert client.get(f"/api/v1/basket-templates/{template_id}").status_code == 200

    assert client.post(
        f"/api/v1/basket-templates/{template_id}/deactivate"
    ).json()["active"] is False
    assert client.post(
        f"/api/v1/basket-templates/{template_id}/activate"
    ).json()["active"] is True
    assert client.patch(
        f"/api/v1/basket-templates/{template_id}",
        json={"name": "Template vazio editado"},
    ).json()["name"] == "Template vazio editado"


def test_template_composition_validates_units_and_aggregates_duplicate_products(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    product = make_product(client, register_m2_cleanup, "Produto UN")
    template = make_template(
        client,
        register_m2_cleanup,
        "Template composto",
        [
            {"product_id": product["id"], "quantity": "2"},
            {"product_id": product["id"], "quantity": "3"},
        ],
    )
    assert len(template["items"]) == 1
    assert Decimal(template["items"][0]["quantity"]) == 5

    invalid = client.post(
        "/api/v1/basket-templates",
        json={
            "name": "Quantidade fracionada",
            "items": [{"product_id": product["id"], "quantity": "0.5"}],
        },
    )
    assert invalid.status_code == 409
    assert client.post(
        "/api/v1/basket-templates",
        json={"name": "   ", "items": []},
    ).status_code == 422


def test_template_inactive_product_is_preserved_editable(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    product = make_product(client, register_m2_cleanup, "Produto template")
    another = make_product(client, register_m2_cleanup, "Produto ativo")
    template = make_template(
        client,
        register_m2_cleanup,
        "Template",
        [
            {"product_id": product["id"], "quantity": "2"},
            {"product_id": another["id"], "quantity": "3"},
        ],
    )
    template_id = template["id"]
    assert client.post(
        f"/api/v1/products/{product['id']}/deactivate"
    ).status_code == 200

    existing = client.get(f"/api/v1/basket-templates/{template_id}").json()
    assert existing["items"][0]["product_active"] is False
    assert Decimal(existing["items"][0]["quantity"]) == 2
    assert client.post(
        f"/api/v1/basket-templates/{template_id}/items",
        json={"product_id": product["id"], "quantity": "1"},
    ).status_code == 409
    updated = client.patch(
        f"/api/v1/basket-templates/{template_id}/items/{product['id']}",
        json={"quantity": "4"},
    )
    assert updated.status_code == 200
    assert Decimal(updated.json()["items"][0]["quantity"]) == 4

    replaced = client.post(
        f"/api/v1/basket-templates/{template_id}/items/{product['id']}/replace",
        json={"product_id": another["id"]},
    )
    assert replaced.status_code == 200
    assert [item["product_id"] for item in replaced.json()["items"]] == [
        another["id"]
    ]
    assert Decimal(replaced.json()["items"][0]["quantity"]) == 7


def test_template_activation_lifecycle(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    product = make_product(client, register_m2_cleanup, "Produto")
    template = make_template(
        client,
        register_m2_cleanup,
        "Template",
        [{"product_id": product["id"], "quantity": "1"}],
    )
    template_id = template["id"]
    assert client.post(
        f"/api/v1/basket-templates/{template_id}/deactivate"
    ).status_code == 200
    assert client.get(f"/api/v1/basket-templates/{template_id}").status_code == 200
    assert client.post(
        f"/api/v1/basket-templates/{template_id}/activate"
    ).status_code == 200


def test_template_list_and_name_are_editable(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    template = make_template(client, register_m2_cleanup, "Antes")
    templates = client.get("/api/v1/basket-templates").json()
    assert any(item["id"] == template["id"] for item in templates)
    assert client.patch(
        f"/api/v1/basket-templates/{template['id']}",
        json={"name": "Depois"},
    ).json()["name"] == "Depois"


def test_template_price_positive_is_persisted_with_two_decimals(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    template = make_template(
        client, register_m2_cleanup, "Template com preço", price="150.00"
    )
    assert template["price"] == "150.00"

    fetched = client.get(f"/api/v1/basket-templates/{template['id']}").json()
    assert fetched["price"] == "150.00"

    templates = client.get("/api/v1/basket-templates").json()
    item = next(t for t in templates if t["id"] == template["id"])
    assert item["price"] == "150.00"


def test_template_created_without_price_has_null_price(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    template = make_template(client, register_m2_cleanup, "Template sem preço")
    assert template["price"] is None

    fetched = client.get(f"/api/v1/basket-templates/{template['id']}").json()
    assert fetched["price"] is None


def test_template_price_zero_is_valid_and_distinct_from_null(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    template = make_template(
        client, register_m2_cleanup, "Template cortesia", price="0.00"
    )
    assert template["price"] == "0.00"
    assert template["price"] is not None

    fetched = client.get(f"/api/v1/basket-templates/{template['id']}").json()
    assert fetched["price"] == "0.00"


def test_template_price_negative_is_rejected(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    res_create = client.post(
        "/api/v1/basket-templates",
        json={"name": "Template negativo", "price": "-10.00"},
    )
    assert res_create.status_code == 422

    template = make_template(client, register_m2_cleanup, "Template para update negativo")
    res_update = client.patch(
        f"/api/v1/basket-templates/{template['id']}",
        json={"price": "-5.00"},
    )
    assert res_update.status_code == 422


def test_template_price_with_more_than_two_decimals_is_rejected(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    res_create = client.post(
        "/api/v1/basket-templates",
        json={"name": "Template muitas casas", "price": "50.125"},
    )
    assert res_create.status_code == 422

    template = make_template(client, register_m2_cleanup, "Template para update casas")
    res_update = client.patch(
        f"/api/v1/basket-templates/{template['id']}",
        json={"price": "99.999"},
    )
    assert res_update.status_code == 422


def test_template_price_normalization(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    t1 = make_template(client, register_m2_cleanup, "Normaliza inteiro", price="12")
    assert t1["price"] == "12.00"

    t2 = make_template(client, register_m2_cleanup, "Normaliza 1 casa", price="12.5")
    assert t2["price"] == "12.50"


def test_template_price_update_and_persistence(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    template = make_template(client, register_m2_cleanup, "Ciclo de preço")
    assert template["price"] is None

    # Atualiza preço para 120.50 mantendo nome
    res1 = client.patch(
        f"/api/v1/basket-templates/{template['id']}",
        json={"price": "120.50"},
    )
    assert res1.status_code == 200
    assert res1.json()["price"] == "120.50"
    assert res1.json()["name"] == "Ciclo de preço"

    # Atualiza preço para 0.00
    res2 = client.patch(
        f"/api/v1/basket-templates/{template['id']}",
        json={"price": "0.00"},
    )
    assert res2.status_code == 200
    assert res2.json()["price"] == "0.00"

    # Atualiza nome mantendo preço
    res3 = client.patch(
        f"/api/v1/basket-templates/{template['id']}",
        json={"name": "Ciclo de preço renomeado"},
    )
    assert res3.status_code == 200
    assert res3.json()["name"] == "Ciclo de preço renomeado"
    assert res3.json()["price"] == "0.00"

    # Atualiza preço para None (remover preço)
    res4 = client.patch(
        f"/api/v1/basket-templates/{template['id']}",
        json={"price": None},
    )
    assert res4.status_code == 200
    assert res4.json()["price"] is None


def test_template_price_isolation_between_instances(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    t1 = make_template(client, register_m2_cleanup, "Template Alfa", price="100.00")
    t2 = make_template(client, register_m2_cleanup, "Template Beta", price="200.00")

    client.patch(
        f"/api/v1/basket-templates/{t1['id']}",
        json={"price": "150.00"},
    )

    t1_updated = client.get(f"/api/v1/basket-templates/{t1['id']}").json()
    t2_fresh = client.get(f"/api/v1/basket-templates/{t2['id']}").json()

    assert t1_updated["price"] == "150.00"
    assert t2_fresh["price"] == "200.00"
