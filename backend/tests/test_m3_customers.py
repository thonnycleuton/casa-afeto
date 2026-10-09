from __future__ import annotations

from collections.abc import Callable, Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.customers.models import Customer
from app.important_dates.models import ImportantDate


@pytest.fixture
def register_customer_cleanup() -> Iterator[Callable[[int, int | None], None]]:
    customer_ids: list[int] = []

    def register(customer_id: int, important_date_id: int | None = None) -> None:
        customer_ids.append(customer_id)

    yield register

    with SessionLocal() as db:
        db.query(ImportantDate).filter(ImportantDate.customer_id.in_(customer_ids)).delete(
            synchronize_session=False
        )
        db.query(Customer).filter(Customer.id.in_(customer_ids)).delete(
            synchronize_session=False
        )
        db.commit()


def make_customer(
    client: TestClient,
    register: Callable[[int, int | None], None],
    *,
    name: str,
    phone: str,
    email: str | None = None,
    notes: str | None = None,
) -> dict:
    response = client.post(
        "/api/v1/customers",
        json={
            "name": name,
            "phone": phone,
            **({"email": email} if email is not None else {}),
            **({"notes": notes} if notes is not None else {}),
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    register(payload["id"])
    return payload


def test_customer_creation_defaults_to_active_and_rejects_status_field(
    client: TestClient, register_customer_cleanup: Callable[[int, int | None], None]
) -> None:
    response = client.post(
        "/api/v1/customers",
        json={"name": "  Maria  ", "phone": "(11) 98888-7766", "status": "INACTIVE"},
    )
    assert response.status_code == 422

    created = make_customer(
        client,
        register_customer_cleanup,
        name="  Maria  ",
        phone="(11) 98888-7766",
    )
    assert created["name"] == "Maria"
    assert created["phone"] == "11988887766"
    assert created["status"] == "ACTIVE"


def test_customer_duplicate_phone_returns_warning_and_status_toggles(
    client: TestClient, register_customer_cleanup: Callable[[int, int | None], None]
) -> None:
    first = make_customer(client, register_customer_cleanup, name="Cliente A", phone="11999990000")
    second = make_customer(client, register_customer_cleanup, name="Cliente B", phone="11 99999-0000")
    assert second["warning"] == {"code": "DUPLICATE_PHONE"}

    updated = client.put(
        f"/api/v1/customers/{first['id']}",
        json={"name": "Cliente A Editado", "phone": "11 99999-0000"},
    )
    assert updated.status_code == 200
    assert updated.json()["warning"] == {"code": "DUPLICATE_PHONE"}

    inactive = client.patch(
        f"/api/v1/customers/{first['id']}/status",
        json={"status": "INACTIVE"},
    )
    assert inactive.status_code == 200
    assert inactive.json()["status"] == "INACTIVE"

    reactivated = client.patch(
        f"/api/v1/customers/{first['id']}/status",
        json={"status": "ACTIVE"},
    )
    assert reactivated.status_code == 200
    assert reactivated.json()["status"] == "ACTIVE"


def test_customer_search_filter_pagination_and_sorting(
    client: TestClient, register_customer_cleanup: Callable[[int, int | None], None]
) -> None:
    marker = "".join(chr(ord("a") + value % 26) for value in uuid4().bytes[:6])
    phone_marker = str(uuid4().int % 1_000_000).zfill(6)
    phone_prefix = f"119{phone_marker}"
    prefix = f"M3-{marker}"
    make_customer(client, register_customer_cleanup, name=f"{prefix} João da Silva", phone=f"{phone_prefix}001")
    make_customer(client, register_customer_cleanup, name=f"{prefix} Ana Maria", phone=f"{phone_prefix}002")
    make_customer(client, register_customer_cleanup, name=f"{prefix} Maria José", phone=f"{phone_prefix}003")
    make_customer(client, register_customer_cleanup, name=f"{prefix} Carlos", phone=f"{phone_prefix}004")
    inactive = make_customer(client, register_customer_cleanup, name=f"{prefix} Zé da Silva", phone=f"{phone_prefix}005")
    client.patch(f"/api/v1/customers/{inactive['id']}/status", json={"status": "INACTIVE"})

    response = client.get(
        "/api/v1/customers",
        params={"search": f"{marker} joa", "status": "ACTIVE"},
    )
    assert response.status_code == 200
    found = response.json()
    assert [item["name"] for item in found] == [f"{prefix} João da Silva"]
    default_status = client.get(
        "/api/v1/customers",
        params={"search": phone_marker},
    )
    assert [item["name"] for item in default_status.json()] == [
        f"{prefix} Ana Maria",
        f"{prefix} Carlos",
        f"{prefix} João da Silva",
        f"{prefix} Maria José",
    ]

    response = client.get(
        "/api/v1/customers",
        params={"search": f"{marker} maria jose", "status": "ALL"},
    )
    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == [f"{prefix} Maria José"]

    response = client.get(
        "/api/v1/customers",
        params={"search": phone_marker, "status": "ALL", "page": 1, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["phone"] == f"{phone_prefix}002"

    no_results = client.get(
        "/api/v1/customers",
        params={"search": "no-customer-with-this-search-term", "status": "ALL"},
    )
    assert no_results.status_code == 200
    assert no_results.json() == []

    response = client.get(
        "/api/v1/customers",
        params={"search": phone_marker, "status": "INACTIVE"},
    )
    assert response.status_code == 200
    assert response.json()[0]["name"] == inactive["name"]


def test_important_date_create_update_and_status_independence(
    client: TestClient, register_customer_cleanup: Callable[[int, int | None], None]
) -> None:
    customer = make_customer(client, register_customer_cleanup, name="Cliente Datas", phone="11900000000")
    recurring = client.post(
        f"/api/v1/customers/{customer['id']}/important-dates",
        json={"description": "Aniversário", "recurring": True, "day": 29, "month": 2},
    )
    assert recurring.status_code == 201
    recurring_data = recurring.json()
    assert recurring_data["recurring"] is True
    assert recurring_data["day"] == 29
    assert recurring_data["month"] == 2
    duplicate_recurring = client.post(
        f"/api/v1/customers/{customer['id']}/important-dates",
        json={"description": "Aniversário", "recurring": True, "day": 29, "month": 2},
    )
    assert duplicate_recurring.status_code == 201

    one_off = client.post(
        f"/api/v1/customers/{customer['id']}/important-dates",
        json={"description": "Evento único", "date": "2027-04-15"},
    )
    assert one_off.status_code == 201

    updated = client.put(
        f"/api/v1/customers/{customer['id']}/important-dates/{recurring_data['id']}",
        json={"description": "Aniversário atualizado", "recurring": True, "day": 29, "month": 2},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Aniversário atualizado"

    converted = client.put(
        f"/api/v1/customers/{customer['id']}/important-dates/{one_off.json()['id']}",
        json={"description": "Evento recorrente", "recurring": True, "day": 3, "month": 4},
    )
    assert converted.status_code == 200
    assert converted.json()["date"] is None
    assert (converted.json()["day"], converted.json()["month"]) == (3, 4)
    converted_back = client.put(
        f"/api/v1/customers/{customer['id']}/important-dates/{one_off.json()['id']}",
        json={"description": "Evento único", "recurring": False, "date": "2027-04-15"},
    )
    assert converted_back.status_code == 200
    assert converted_back.json()["day"] is None
    assert converted_back.json()["month"] is None

    disabled = client.patch(
        f"/api/v1/customers/{customer['id']}/important-dates/{recurring_data['id']}/status",
        json={"status": "INACTIVE"},
    )
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "INACTIVE"

    customer_response = client.patch(
        f"/api/v1/customers/{customer['id']}/status",
        json={"status": "INACTIVE"},
    )
    assert customer_response.status_code == 200
    listed_dates = client.get(
        f"/api/v1/customers/{customer['id']}/important-dates"
    ).json()
    date_statuses = {date_record["id"]: date_record["status"] for date_record in listed_dates}
    assert len(listed_dates) == 3
    assert date_statuses[recurring_data["id"]] == "INACTIVE"
    assert date_statuses[one_off.json()["id"]] == "ACTIVE"
    assert date_statuses[duplicate_recurring.json()["id"]] == "ACTIVE"

    reactivated = client.patch(
        f"/api/v1/customers/{customer['id']}/status",
        json={"status": "ACTIVE"},
    )
    assert reactivated.json()["status"] == "ACTIVE"
    reactivated_dates = client.get(
        f"/api/v1/customers/{customer['id']}/important-dates"
    ).json()
    assert {item["id"]: item["status"] for item in reactivated_dates} == date_statuses


def test_customer_validation_inactive_edit_and_contact_clearing(
    client: TestClient, register_customer_cleanup: Callable[[int, int | None], None]
) -> None:
    invalid = client.post(
        "/api/v1/customers",
        json={"name": "   ", "phone": "(---)"},
    )
    assert invalid.status_code == 422

    customer = make_customer(
        client,
        register_customer_cleanup,
        name="  Cliente Editável  ",
        phone="(11) 98888-1234",
        email="cliente@example.com",
        notes="  Observação  ",
    )
    assert customer["name"] == "Cliente Editável"
    assert customer["phone"] == "11988881234"
    assert customer["notes"] == "Observação"

    invalid_email = client.post(
        "/api/v1/customers",
        json={"name": "Email inválido", "phone": "11911111111", "email": "not-an-email"},
    )
    assert invalid_email.status_code == 422

    client.patch(
        f"/api/v1/customers/{customer['id']}/status",
        json={"status": "INACTIVE"},
    )
    updated = client.put(
        f"/api/v1/customers/{customer['id']}",
        json={"name": "Cliente Inativo Editado", "phone": "11-98888-1234", "email": None, "notes": ""},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "INACTIVE"
    assert updated.json()["name"] == "Cliente Inativo Editado"
    assert updated.json()["email"] is None
    assert updated.json()["notes"] is None

    clear_optional = client.put(
        f"/api/v1/customers/{customer['id']}",
        json={"email": None},
    )
    assert clear_optional.status_code == 200
    assert clear_optional.json()["name"] == "Cliente Inativo Editado"


def test_important_date_validation_and_inactive_customer_operations(
    client: TestClient, register_customer_cleanup: Callable[[int, int | None], None]
) -> None:
    customer = make_customer(
        client, register_customer_cleanup, name="Cliente Inativo Datas", phone="11910000000"
    )
    client.patch(
        f"/api/v1/customers/{customer['id']}/status",
        json={"status": "INACTIVE"},
    )

    invalid_recurring = client.post(
        f"/api/v1/customers/{customer['id']}/important-dates",
        json={"description": "Data inválida", "recurring": True, "day": 30, "month": 2},
    )
    assert invalid_recurring.status_code == 422

    past_date = client.post(
        f"/api/v1/customers/{customer['id']}/important-dates",
        json={"description": "Data passada", "date": "2020-01-02"},
    )
    assert past_date.status_code == 201
    assert past_date.json()["date"] == "2020-01-02"
    assert past_date.json()["status"] == "ACTIVE"

    recurring = client.post(
        f"/api/v1/customers/{customer['id']}/important-dates",
        json={"description": "29 de fevereiro", "recurring": True, "day": 29, "month": 2},
    )
    assert recurring.status_code == 201
    assert (recurring.json()["day"], recurring.json()["month"]) == (29, 2)

    other_customer = make_customer(
        client, register_customer_cleanup, name="Outro Cliente", phone="11910000001"
    )
    foreign_date = client.put(
        f"/api/v1/customers/{other_customer['id']}/important-dates/{past_date.json()['id']}",
        json={"description": "Data passada", "recurring": False, "date": "2020-01-02"},
    )
    assert foreign_date.status_code == 404

    assert client.get(f"/api/v1/customers/{customer['id']}").json()["status"] == "INACTIVE"
    assert client.delete(
        f"/api/v1/customers/{customer['id']}/important-dates/{past_date.json()['id']}"
    ).status_code == 405
    missing_customer = 2_147_483_647
    assert client.get(f"/api/v1/customers/{missing_customer}").status_code == 404
    assert client.post(
        f"/api/v1/customers/{missing_customer}/important-dates",
        json={"description": "Não deve persistir", "date": "2027-04-15"},
    ).status_code == 404
    assert client.put(
        f"/api/v1/customers/{customer['id']}/important-dates/{missing_customer}",
        json={"description": "Não encontrada", "recurring": False, "date": "2027-04-15"},
    ).status_code == 404
    assert client.delete(f"/api/v1/customers/{customer['id']}").status_code == 405
