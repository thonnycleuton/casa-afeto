from collections.abc import Callable, Iterator
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.baskets.models import Basket, BasketItem, BasketTemplate, BasketTemplateItem
from app.core.database import SessionLocal
from app.products.models import InventoryMovement, Product


@pytest.fixture
def register_m2_cleanup() -> Iterator[Callable[[str, int], None]]:
    registered: dict[str, list[int]] = {
        "product": [],
        "template": [],
        "basket": [],
    }

    def register(kind: str, identifier: int) -> None:
        registered[kind].append(identifier)

    yield register
    with SessionLocal() as db:
        db.query(BasketItem).filter(
            BasketItem.basket_id.in_(registered["basket"])
        ).delete(synchronize_session=False)
        db.query(Basket).filter(Basket.id.in_(registered["basket"])).delete(
            synchronize_session=False
        )
        db.query(BasketTemplateItem).filter(
            BasketTemplateItem.template_id.in_(registered["template"])
        ).delete(synchronize_session=False)
        db.query(BasketTemplate).filter(
            BasketTemplate.id.in_(registered["template"])
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


def make_basket(
    client: TestClient,
    register: Callable[[str, int], None],
    name: str,
    *,
    template_id: int | None = None,
    items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/baskets",
        json={
            "name": name,
            "template_id": template_id,
            **({"items": items or []} if template_id is None else {}),
        },
    )
    assert response.status_code == 201, response.text
    basket = response.json()
    register("basket", basket["id"])
    return basket


def test_template_empty_active_lifecycle_and_empty_cannot_create_basket(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    template = make_template(client, register_m2_cleanup, "Template vazio")
    template_id = template["id"]
    assert template["active"] is True
    assert template["items"] == []
    assert client.get(f"/api/v1/basket-templates/{template_id}").status_code == 200

    rejected = client.post(
        "/api/v1/baskets",
        json={"name": "Não pode usar vazio", "template_id": template_id},
    )
    assert rejected.status_code == 409

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


def test_template_inactive_product_is_preserved_editable_and_blocks_basket_creation(
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
    assert client.post(
        "/api/v1/baskets",
        json={"name": "Blocked", "template_id": template_id},
    ).status_code == 409

    replaced = client.post(
        f"/api/v1/basket-templates/{template_id}/items/{product['id']}/replace",
        json={"product_id": another["id"]},
    )
    assert replaced.status_code == 200
    assert [item["product_id"] for item in replaced.json()["items"]] == [
        another["id"]
    ]
    assert Decimal(replaced.json()["items"][0]["quantity"]) == 7
    created = client.post(
        "/api/v1/baskets",
        json={"name": "Template corrigido", "template_id": template_id},
    )
    assert created.status_code == 201
    register_m2_cleanup("basket", created.json()["id"])
    assert Decimal(created.json()["items"][0]["quantity"]) == 7


def test_template_activation_and_template_containing_inactive_product_are_enforced(
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
    assert client.post(
        "/api/v1/baskets",
        json={"name": "Inactive template", "template_id": template_id},
    ).status_code == 409
    assert client.get(f"/api/v1/basket-templates/{template_id}").status_code == 200
    assert client.post(
        f"/api/v1/basket-templates/{template_id}/activate"
    ).status_code == 200


def test_basket_can_be_empty_and_template_composition_is_copied_independently(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    product_a = make_product(client, register_m2_cleanup, "Produto A")
    product_b = make_product(client, register_m2_cleanup, "Produto B")
    empty = make_basket(client, register_m2_cleanup, "Cesta vazia")
    assert empty["items"] == []

    template = make_template(
        client,
        register_m2_cleanup,
        "Template original",
        [{"product_id": product_a["id"], "quantity": "2"}],
    )
    basket = make_basket(
        client, register_m2_cleanup, "Cópia", template_id=template["id"]
    )
    basket_id = basket["id"]
    assert basket["template_id"] == template["id"]
    assert Decimal(basket["items"][0]["quantity"]) == 2

    assert client.post(
        f"/api/v1/basket-templates/{template['id']}/items",
        json={"product_id": product_b["id"], "quantity": "3"},
    ).status_code == 200
    assert len(client.get(f"/api/v1/baskets/{basket_id}").json()["items"]) == 1

    assert client.post(
        f"/api/v1/baskets/{basket_id}/items",
        json={"product_id": product_b["id"], "quantity": "1"},
    ).status_code == 200
    template_after = client.get(
        f"/api/v1/basket-templates/{template['id']}"
    ).json()
    assert len(template_after["items"]) == 2

    cleared = client.delete(
        f"/api/v1/baskets/{basket_id}/items/{product_a['id']}"
    )
    assert cleared.status_code == 200
    cleared = client.delete(
        f"/api/v1/baskets/{basket_id}/items/{product_b['id']}"
    )
    assert cleared.status_code == 200
    assert cleared.json()["items"] == []


def test_basket_composition_mutations_aggregate_replace_and_preserve_inactive_items(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    product_a = make_product(client, register_m2_cleanup, "Produto A")
    product_b = make_product(client, register_m2_cleanup, "Produto B")
    product_c = make_product(client, register_m2_cleanup, "Produto C")
    basket = make_basket(
        client,
        register_m2_cleanup,
        "Composição",
        items=[
            {"product_id": product_a["id"], "quantity": "2"},
            {"product_id": product_b["id"], "quantity": "3"},
        ],
    )
    basket_id = basket["id"]

    added = client.post(
        f"/api/v1/baskets/{basket_id}/items",
        json={"product_id": product_a["id"], "quantity": "4"},
    ).json()
    assert len(added["items"]) == 2
    assert Decimal(next(i for i in added["items"] if i["product_id"] == product_a["id"])["quantity"]) == 6

    replaced = client.post(
        f"/api/v1/baskets/{basket_id}/items/{product_a['id']}/replace",
        json={"product_id": product_b["id"]},
    )
    assert replaced.status_code == 200
    rows = {item["product_id"]: Decimal(item["quantity"]) for item in replaced.json()["items"]}
    assert product_a["id"] not in rows
    assert rows[product_b["id"]] == 9

    replaced = client.post(
        f"/api/v1/baskets/{basket_id}/items/{product_b['id']}/replace",
        json={"product_id": product_c["id"]},
    )
    assert replaced.status_code == 200
    assert replaced.json()["items"][0]["product_id"] == product_c["id"]
    assert Decimal(replaced.json()["items"][0]["quantity"]) == 9

    assert client.post(
        f"/api/v1/products/{product_c['id']}/deactivate"
    ).status_code == 200
    inactive_edit = client.patch(
        f"/api/v1/baskets/{basket_id}/items/{product_c['id']}",
        json={"quantity": "5"},
    )
    assert inactive_edit.status_code == 200
    assert inactive_edit.json()["items"][0]["product_active"] is False
    assert Decimal(inactive_edit.json()["items"][0]["quantity"]) == 5
    assert client.post(
        f"/api/v1/baskets/{basket_id}/items",
        json={"product_id": product_c["id"], "quantity": "1"},
    ).status_code == 409
    assert client.delete(
        f"/api/v1/baskets/{basket_id}/items/{product_c['id']}"
    ).json()["items"] == []


def test_stock_shortage_is_informative_and_never_mutated_by_m2(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    product = make_product(client, register_m2_cleanup, "Produto com estoque")
    assert client.post(
        f"/api/v1/products/{product['id']}/inventory/entries",
        json={"quantity": "2"},
    ).status_code == 201
    before = client.get(
        f"/api/v1/products/{product['id']}/inventory/movements"
    ).json()

    basket = make_basket(
        client,
        register_m2_cleanup,
        "Insuficiente",
        items=[{"product_id": product["id"], "quantity": "5"}],
    )
    item = basket["items"][0]
    assert item["stock_available"] is False
    assert Decimal(item["stock_shortage"]) == 3
    assert Decimal(item["inventory_balance"]) == 2
    assert client.get(
        f"/api/v1/products/{product['id']}/inventory/balance"
    ).json()["quantity"] == "2"
    assert client.get(
        f"/api/v1/products/{product['id']}/inventory/movements"
    ).json() == before


def test_replace_rejects_incompatible_target_unit_without_partial_changes(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    fractional = make_product(client, register_m2_cleanup, "Produto decimal", "KG")
    whole = make_product(client, register_m2_cleanup, "Produto inteiro", "UN")
    basket = make_basket(
        client,
        register_m2_cleanup,
        "Unidades diferentes",
        items=[
            {"product_id": fractional["id"], "quantity": "0.5"},
            {"product_id": whole["id"], "quantity": "2"},
        ],
    )

    rejected = client.post(
        f"/api/v1/baskets/{basket['id']}/items/{fractional['id']}/replace",
        json={"product_id": whole["id"]},
    )
    assert rejected.status_code == 409
    saved = client.get(f"/api/v1/baskets/{basket['id']}").json()
    quantities = {item["product_id"]: Decimal(item["quantity"]) for item in saved["items"]}
    assert quantities == {fractional["id"]: Decimal("0.5"), whole["id"]: Decimal("2")}


def test_basket_and_template_lists_and_names_are_editable(
    client: TestClient, register_m2_cleanup: Callable[[str, int], None]
) -> None:
    template = make_template(client, register_m2_cleanup, "Antes")
    basket = make_basket(client, register_m2_cleanup, "Cesta antes")
    templates = client.get("/api/v1/basket-templates").json()
    baskets = client.get("/api/v1/baskets").json()
    assert any(item["id"] == template["id"] for item in templates)
    assert any(item["id"] == basket["id"] for item in baskets)
    assert client.patch(
        f"/api/v1/basket-templates/{template['id']}",
        json={"name": "Depois"},
    ).json()["name"] == "Depois"
    assert client.patch(
        f"/api/v1/baskets/{basket['id']}",
        json={"name": "Cesta depois"},
    ).json()["name"] == "Cesta depois"


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
