from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier
from typing import Any, Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.database import engine
from app.main import app


def create_product(
    client: TestClient,
    register_product: Callable[[int], None],
    *,
    name: str = "test-product",
    unit: str = "UN",
) -> dict[str, Any]:
    response = client.post(
        "/api/v1/products", json={"name": name, "base_unit": unit}
    )
    assert response.status_code == 201, response.text
    product = response.json()
    register_product(product["id"])
    return product


def get_balance(client: TestClient, product_id: int) -> Decimal:
    response = client.get(
        f"/api/v1/products/{product_id}/inventory/balance"
    )
    assert response.status_code == 200
    return Decimal(response.json()["quantity"])


def test_product_creation_validation_and_duplicate_names(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    first = create_product(
        client, register_product_for_cleanup, name="test-same-name"
    )
    second = create_product(
        client, register_product_for_cleanup, name="test-same-name"
    )
    assert first["id"] != second["id"]
    assert first["active"] is True
    assert first["inventory_balance"] == "0"

    for payload in (
        {"base_unit": "UN"},
        {"name": " ", "base_unit": "UN"},
        {"name": "test-invalid-unit", "base_unit": "BOX"},
        {"name": "test-missing-unit"},
        {"name": "test-unapproved-field", "base_unit": "UN", "price": "1.00"},
    ):
        assert client.post("/api/v1/products", json=payload).status_code == 422


@pytest.mark.parametrize("unit", ["UN", "KG", "G", "L", "ML"])
def test_all_supported_product_units(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
    unit: str,
) -> None:
    product = create_product(client, register_product_for_cleanup, unit=unit)
    assert product["base_unit"] == unit


def test_product_edit_activation_deactivation_and_unit_lock(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    edited = client.patch(
        f"/api/v1/products/{product_id}",
        json={"name": "test-edited", "base_unit": "KG"},
    )
    assert edited.status_code == 200
    assert edited.json()["name"] == "test-edited"
    assert edited.json()["base_unit"] == "KG"

    assert client.post(
        f"/api/v1/products/{product_id}/deactivate"
    ).json()["active"] is False
    assert client.post(
        f"/api/v1/products/{product_id}/activate"
    ).json()["active"] is True

    entry = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "1.25"},
    )
    assert entry.status_code == 201
    rejected = client.patch(
        f"/api/v1/products/{product_id}", json={"base_unit": "G"}
    )
    assert rejected.status_code == 409
    assert client.patch(
        f"/api/v1/products/{product_id}", json={"name": "test-renamed"}
    ).status_code == 200
    assert get_balance(client, product_id) == Decimal("1.25")


def test_product_search_is_case_insensitive_and_substring_based(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    prefix = f"search-{uuid4().hex}"
    matching_names = [
        f"{prefix}-Chocolate",
        f"{prefix}-CHOCOLATE BAR",
        f"{prefix}-Choco Cake",
    ]
    matching_products = [
        create_product(client, register_product_for_cleanup, name=name)
        for name in matching_names
    ]
    create_product(client, register_product_for_cleanup, name=f"{prefix}-Vanilla")

    response = client.get("/api/v1/products", params={"search": "cHoC"})
    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.json()}
    assert {product["id"] for product in matching_products} <= returned_ids
    assert not any(
        item["name"] == f"{prefix}-Vanilla" for item in response.json()
    )
    assert client.get(
        "/api/v1/products", params={"search": "no matching product"}
    ).json() == []


@pytest.mark.parametrize("quantity", ["0", "-1"])
def test_invalid_entries_have_no_side_effects(
    client: TestClient,
    register_product_for_cleanup: Callable[[int], None],
    quantity: str,
) -> None:
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]
    response = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": quantity},
    )
    assert response.status_code == 422
    assert get_balance(client, product_id) == 0
    assert client.get(
        f"/api/v1/products/{product_id}/inventory/movements"
    ).json() == []


def test_entry_decimal_rules_and_product_state(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    fractional_unit = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "2.5"},
    )
    assert fractional_unit.status_code == 409
    assert client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "3"},
    ).status_code == 201

    inactive = client.post(f"/api/v1/products/{product_id}/deactivate")
    assert inactive.status_code == 200
    inactive_product = next(
        item
        for item in client.get("/api/v1/products").json()
        if item["id"] == product_id
    )
    assert inactive_product["active"] is False
    rejected = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "1"},
    )
    assert rejected.status_code == 409
    rejected_adjustment = client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "-1"},
    )
    assert rejected_adjustment.status_code == 409
    assert client.post(f"/api/v1/products/{product_id}/activate").json()["active"] is True
    nonexistent = client.post(
        "/api/v1/products/2147483647/inventory/entries",
        json={"quantity": "1"},
    )
    assert nonexistent.status_code == 404
    assert get_balance(client, product_id) == 3
    assert len(
        client.get(
            f"/api/v1/products/{product_id}/inventory/movements"
        ).json()
    ) == 1


def test_adjustments_history_availability_and_immutable_api(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]
    create_entry = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "4"},
    )
    assert create_entry.status_code == 201

    positive = client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "2"},
    )
    negative = client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "-6"},
    )
    assert positive.status_code == 201
    assert negative.status_code == 201
    assert get_balance(client, product_id) == 0

    insufficient = client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "-1"},
    )
    zero = client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "0"},
    )
    assert insufficient.status_code == 409
    assert zero.status_code == 422

    entry = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "10"},
    )
    before = client.get(
        f"/api/v1/products/{product_id}/inventory/movements"
    ).json()
    available = client.post(
        f"/api/v1/products/{product_id}/inventory/availability",
        json={"quantity": "4"},
    ).json()
    short = client.post(
        f"/api/v1/products/{product_id}/inventory/availability",
        json={"quantity": "12"},
    ).json()
    assert available["available"] is True
    assert Decimal(available["shortage"]) == 0
    assert short["available"] is False
    assert Decimal(short["shortage"]) == 2
    assert get_balance(client, product_id) == 10
    assert len(
        client.get(
            f"/api/v1/products/{product_id}/inventory/movements"
        ).json()
    ) == len(before)

    history = client.get(
        f"/api/v1/products/{product_id}/inventory/movements"
    ).json()
    assert [movement["type"] for movement in history] == [
        "ENTRY",
        "ADJUSTMENT",
        "ADJUSTMENT",
        "ENTRY",
    ]
    assert [Decimal(movement["quantity"]) for movement in history] == [
        Decimal("4"),
        Decimal("2"),
        Decimal("-6"),
        Decimal("10"),
    ]
    movement_id = entry.json()["id"]
    for method in ("put", "patch", "delete"):
        response = client.request(
            method.upper(),
            f"/api/v1/inventory-movements/{movement_id}",
            json={"quantity": "99"},
        )
        assert response.status_code == 404
    assert get_balance(client, product_id) == 10


def test_decimal_precision_is_preserved(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    product = create_product(
        client, register_product_for_cleanup, unit="KG"
    )
    product_id = product["id"]
    quantity = "0.123456789123456789"
    response = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": quantity},
    )
    assert response.status_code == 201
    assert Decimal(response.json()["quantity"]) == Decimal(quantity)
    assert get_balance(client, product_id) == Decimal(quantity)


def test_decimal_adjustment_and_fractional_unit_adjustment_rules(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    fractional_product = create_product(
        client, register_product_for_cleanup, unit="KG"
    )
    product_id = fractional_product["id"]
    assert client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "1.5"},
    ).status_code == 201
    adjustment = client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "-0.25"},
    )
    assert adjustment.status_code == 201
    assert Decimal(adjustment.json()["quantity"]) == Decimal("-0.25")
    assert get_balance(client, product_id) == Decimal("1.25")

    whole_product = create_product(client, register_product_for_cleanup)
    rejected = client.post(
        f"/api/v1/products/{whole_product['id']}/inventory/adjustments",
        json={"quantity": "0.5"},
    )
    assert rejected.status_code == 409
    assert get_balance(client, whole_product["id"]) == 0


def test_concurrent_adjustments_cannot_make_inventory_negative(
    register_product_for_cleanup: Callable[[int], None],
) -> None:
    with TestClient(app) as client:
        product = create_product(client, register_product_for_cleanup)
        product_id = product["id"]
        assert client.post(
            f"/api/v1/products/{product_id}/inventory/entries",
            json={"quantity": "4"},
        ).status_code == 201

    lock_barrier = Barrier(2)
    lock_queries: list[str] = []

    def synchronize_inventory_locks(
        _connection: Any,
        _cursor: Any,
        statement: str,
        _parameters: Any,
        _context: Any,
        _executemany: bool,
    ) -> None:
        if "FOR UPDATE" in statement.upper():
            lock_queries.append(statement)
            lock_barrier.wait(timeout=10)

    def reduce_inventory() -> int:
        with TestClient(app) as concurrent_client:
            response = concurrent_client.post(
                f"/api/v1/products/{product_id}/inventory/adjustments",
                json={"quantity": "-3"},
            )
            return response.status_code

    event.listen(engine, "before_cursor_execute", synchronize_inventory_locks)
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(lambda _: reduce_inventory(), range(2)))
    finally:
        event.remove(engine, "before_cursor_execute", synchronize_inventory_locks)

    assert len(lock_queries) == 2
    assert statuses.count(201) == 1
    assert statuses.count(409) == 1
    with TestClient(app) as client:
        assert get_balance(client, product_id) == 1
        history = client.get(
            f"/api/v1/products/{product_id}/inventory/movements"
        ).json()
    assert len(history) == 2
    assert sum(Decimal(movement["quantity"]) for movement in history) == 1


def test_ac39_complete_m1_operational_flow(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    product = create_product(
        client, register_product_for_cleanup, name="test-Chocolate"
    )
    product_id = product["id"]
    assert client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": "20"},
    ).status_code == 201
    assert client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "-3"},
    ).status_code == 201
    assert get_balance(client, product_id) == 17

    availability = client.post(
        f"/api/v1/products/{product_id}/inventory/availability",
        json={"quantity": "20"},
    ).json()
    assert availability == {
        "product_id": product_id,
        "available": False,
        "available_quantity": "17",
        "required_quantity": "20",
        "shortage": "3",
        "base_unit": "UN",
    }
    assert client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "-18"},
    ).status_code == 409

    history = client.get(
        f"/api/v1/products/{product_id}/inventory/movements"
    ).json()
    assert [(item["type"], Decimal(item["quantity"])) for item in history] == [
        ("ENTRY", Decimal("20")),
        ("ADJUSTMENT", Decimal("-3")),
    ]
    deactivated = client.post(f"/api/v1/products/{product_id}/deactivate")
    assert deactivated.json()["active"] is False
    listed = client.get(
        "/api/v1/products", params={"search": "choc"}
    ).json()
    assert any(item["id"] == product_id for item in listed)
    assert get_balance(client, product_id) == 17


def test_inventory_zero_balance_and_rejection_workflow(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    product = create_product(client, register_product_for_cleanup)
    product_id = product["id"]

    for path, quantity, expected_balance in (
        ("entries", "10", Decimal("10")),
        ("adjustments", "-3", Decimal("7")),
        ("adjustments", "-7", Decimal("0")),
    ):
        response = client.post(
            f"/api/v1/products/{product_id}/inventory/{path}",
            json={"quantity": quantity},
        )
        assert response.status_code == 201
        assert get_balance(client, product_id) == expected_balance

    history_before_rejection = client.get(
        f"/api/v1/products/{product_id}/inventory/movements"
    ).json()
    rejected = client.post(
        f"/api/v1/products/{product_id}/inventory/adjustments",
        json={"quantity": "-1"},
    )
    assert rejected.status_code == 409
    assert get_balance(client, product_id) == 0
    assert client.get(
        f"/api/v1/products/{product_id}/inventory/movements"
    ).json() == history_before_rejection


def test_documented_validation_workflow_suco_test(
    client: TestClient, register_product_for_cleanup: Callable[[int], None]
) -> None:
    product = create_product(
        client, register_product_for_cleanup, name="test-Suco Test"
    )
    product_id = product["id"]
    for movement, quantity in (
        ("entries", "20"),
        ("entries", "10"),
        ("adjustments", "-5"),
    ):
        response = client.post(
            f"/api/v1/products/{product_id}/inventory/{movement}",
            json={"quantity": quantity},
        )
        assert response.status_code == 201
    assert get_balance(client, product_id) == 25

    sufficient = client.post(
        f"/api/v1/products/{product_id}/inventory/availability",
        json={"quantity": "20"},
    ).json()
    insufficient = client.post(
        f"/api/v1/products/{product_id}/inventory/availability",
        json={"quantity": "30"},
    ).json()
    assert sufficient["available"] is True
    assert insufficient["available"] is False
    assert Decimal(insufficient["shortage"]) == 5
    assert get_balance(client, product_id) == 25
    assert len(
        client.get(
            f"/api/v1/products/{product_id}/inventory/movements"
        ).json()
    ) == 3
