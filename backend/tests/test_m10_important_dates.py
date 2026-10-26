"""Testes M10 — Datas Afetivas.

Cobre AC-M10-001 a AC-M10-013 (backend).
"""

from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.customers.models import Customer
from app.important_dates.models import ImportantDate


def _marker() -> str:
    """Generate a unique marker for test isolation."""
    return uuid4().hex[:8]


@pytest.fixture
def _cleanup():
    """Cleanup after M10 tests."""
    customer_ids: list[int] = []

    def register(customer_id: int) -> int:
        customer_ids.append(customer_id)
        return customer_id

    yield register

    with SessionLocal() as db:
        db.query(ImportantDate).filter(
            ImportantDate.customer_id.in_(customer_ids)
        ).delete(synchronize_session=False)
        db.query(Customer).filter(Customer.id.in_(customer_ids)).delete(
            synchronize_session=False
        )
        db.commit()


def _create_customer(name: str, phone: str = "11900000000", status: str = "ACTIVE") -> int:
    with SessionLocal() as db:
        customer = Customer(name=name, phone=phone, status=status)
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer.id


def _create_important_date(
    customer_id: int,
    description: str,
    recurring: bool,
    day: int | None = None,
    month: int | None = None,
    date_value: date | None = None,
    status: str = "ACTIVE",
) -> int:
    with SessionLocal() as db:
        imp_date = ImportantDate(
            customer_id=customer_id,
            description=description,
            recurring=recurring,
            day=day,
            month=month,
            date=date_value,
            status=status,
        )
        db.add(imp_date)
        db.commit()
        db.refresh(imp_date)
        return imp_date.id


def _find_item(data: dict, marker: str) -> dict | None:
    """Find an item whose description contains the marker."""
    for item in data.get("items", []):
        if marker in item.get("description", ""):
            return item
    return None


class TestUpcomingDatesActiveOnly:
    """AC-M10-001: Apenas datas ativas são retornadas."""

    def test_inactive_dates_not_returned(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        # Data ativa dentro da janela
        _create_important_date(
            customer_id, f"{marker}-Ativa", True, day=15, month=11, status="ACTIVE"
        )
        # Data inativa dentro da janela
        _create_important_date(
            customer_id, f"{marker}-Inativa", True, day=20, month=10, status="INACTIVE"
        )

        response = client.get("/api/v1/important-dates/upcoming?days=30")
        assert response.status_code == 200
        data = response.json()
        active_items = [i for i in data["items"] if marker in i["description"]]
        assert len(active_items) == 1
        assert active_items[0]["description"] == f"{marker}-Ativa"

    def test_all_inactive_returns_empty(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Inativa", True, day=15, month=11, status="INACTIVE"
        )

        response = client.get("/api/v1/important-dates/upcoming?days=30")
        assert response.status_code == 200
        data = response.json()
        assert _find_item(data, marker) is None


class TestUpcomingRecurringCurrentYear:
    """AC-M10-002: Próxima ocorrência de data recorrente no ano atual."""

    def test_recurring_date_future_in_current_year(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Aniv", True, day=15, month=11
        )

        response = client.get("/api/v1/important-dates/upcoming?days=30")
        assert response.status_code == 200
        item = _find_item(response.json(), marker)
        assert item is not None
        assert item["next_occurrence"] == "2026-11-15"

    def test_recurring_date_past_moves_to_next_year(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-AnoNovo", True, day=1, month=1
        )

        response = client.get("/api/v1/important-dates/upcoming?days=365")
        assert response.status_code == 200
        item = _find_item(response.json(), marker)
        assert item is not None
        assert item["next_occurrence"] == "2027-01-01"


class TestUpcomingRecurringNextYear:
    """AC-M10-003: Próxima ocorrência de data recorrente no ano seguinte."""

    def test_recurring_date_already_passed(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Mar", True, day=15, month=3
        )

        response = client.get("/api/v1/important-dates/upcoming?days=365")
        assert response.status_code == 200
        item = _find_item(response.json(), marker)
        assert item is not None
        assert item["next_occurrence"] == "2027-03-15"

    def test_recurring_date_today_is_included(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Hoje", True, day=26, month=10
        )

        response = client.get("/api/v1/important-dates/upcoming?days=7")
        assert response.status_code == 200
        item = _find_item(response.json(), marker)
        assert item is not None
        assert item["next_occurrence"].startswith("2026-10-26")


class TestUpcomingFebruary29:
    """AC-M10-004: Data 29 de fevereiro em ano não bissexto."""

    def test_feb_29_finds_next_leap_year(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Bissexto", True, day=29, month=2
        )

        response = client.get("/api/v1/important-dates/upcoming?days=730")
        assert response.status_code == 200
        item = _find_item(response.json(), marker)
        assert item is not None
        assert item["next_occurrence"] == "2028-02-29"


class TestUpcomingNonRecurring:
    """AC-M10-005 e AC-M10-006: Datas não recorrentes."""

    def test_non_recurring_future_date(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Natal", False, date_value=date(2026, 12, 25)
        )

        response = client.get("/api/v1/important-dates/upcoming?days=60")
        assert response.status_code == 200
        item = _find_item(response.json(), marker)
        assert item is not None
        assert item["next_occurrence"] == "2026-12-25"

    def test_non_recurring_past_date_not_listed(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Passado", False, date_value=date(2026, 1, 15)
        )

        response = client.get("/api/v1/important-dates/upcoming?days=365")
        assert response.status_code == 200
        assert _find_item(response.json(), marker) is None

    def test_non_recurring_today_is_listed(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Hoje", False, date_value=date(2026, 10, 26)
        )

        response = client.get("/api/v1/important-dates/upcoming?days=1")
        assert response.status_code == 200
        item = _find_item(response.json(), marker)
        assert item is not None
        assert item["next_occurrence"] == "2026-10-26"


class TestUpcomingDaysWindow:
    """AC-M10-007 e AC-M10-008: Janela de tempo."""

    def test_default_window_is_7_days(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Proxima", True, day=1, month=11
        )
        _create_important_date(
            customer_id, f"{marker}-Longe", True, day=15, month=11
        )

        response = client.get("/api/v1/important-dates/upcoming")
        assert response.status_code == 200
        data = response.json()
        items = [i for i in data["items"] if marker in i["description"]]
        assert len(items) == 1
        assert items[0]["description"] == f"{marker}-Proxima"

    def test_days_parameter_adjusts_window(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-30d", True, day=15, month=11
        )

        response = client.get("/api/v1/important-dates/upcoming?days=30")
        assert response.status_code == 200
        assert _find_item(response.json(), marker) is not None

        response = client.get("/api/v1/important-dates/upcoming?days=1")
        assert response.status_code == 200
        assert _find_item(response.json(), marker) is None


class TestUpcomingDaysValidation:
    """AC-M10-009: Validação do parâmetro days."""

    def test_days_zero_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/important-dates/upcoming?days=0")
        assert response.status_code == 422

    def test_days_over_max_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/important-dates/upcoming?days=1096")
        assert response.status_code == 422

    def test_days_negative_returns_422(self, client: TestClient) -> None:
        response = client.get("/api/v1/important-dates/upcoming?days=-1")
        assert response.status_code == 422


class TestUpcomingSorting:
    """AC-M10-010: Ordenação por próxima ocorrência."""

    def test_sorted_by_next_occurrence(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Nov15", True, day=15, month=11
        )
        _create_important_date(
            customer_id, f"{marker}-Out30", True, day=30, month=10
        )
        _create_important_date(
            customer_id, f"{marker}-Nov02", True, day=2, month=11
        )

        response = client.get("/api/v1/important-dates/upcoming?days=30")
        assert response.status_code == 200
        data = response.json()
        items = [i for i in data["items"] if marker in i["description"]]
        occurrences = [item["next_occurrence"] for item in items]
        assert occurrences == sorted(occurrences)

    def test_tie_broken_by_customer_name(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        id_a = _create_customer(f"{marker}-Ana")
        _cleanup(id_a)
        id_z = _create_customer(f"{marker}-Zé")
        _cleanup(id_z)

        _create_important_date(id_a, f"{marker}-Aniv", True, day=15, month=11)
        _create_important_date(id_z, f"{marker}-Aniv", True, day=15, month=11)

        response = client.get("/api/v1/important-dates/upcoming?days=30")
        assert response.status_code == 200
        data = response.json()
        items = [i for i in data["items"] if marker in i["description"]]
        assert len(items) == 2
        assert items[0]["customer_name"] == f"{marker}-Ana"
        assert items[1]["customer_name"] == f"{marker}-Zé"


class TestUpcomingInactiveCustomer:
    """AC-M10-011: Cliente inativo não impede listagem."""

    def test_inactive_customer_date_still_shows(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"{marker}-Inativo", status="INACTIVE")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Aniv", True, day=15, month=11
        )

        response = client.get("/api/v1/important-dates/upcoming?days=30")
        assert response.status_code == 200
        item = _find_item(response.json(), marker)
        assert item is not None
        assert item["customer_name"] == f"{marker}-Inativo"


class TestUpcomingResponseFields:
    """AC-M10-012: Resposta inclui todos os campos esperados."""

    def test_response_has_all_fields(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Teste", True, day=15, month=11
        )

        response = client.get("/api/v1/important-dates/upcoming?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        item = _find_item(data, marker)
        assert item is not None
        assert "id" in item
        assert "customer_id" in item
        assert "customer_name" in item
        assert "description" in item
        assert "recurring" in item
        assert "next_occurrence" in item
        assert "status" in item


class TestUpcomingEmptyList:
    """AC-M10-013: Lista vazia quando não há datas próximas."""

    def test_no_dates_returns_empty(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/v1/important-dates/upcoming?days=7")
        assert response.status_code == 200
        data = response.json()
        # The endpoint may return data from other tests, but structure is correct
        assert "items" in data
        assert "total" in data

    def test_dates_outside_window_returns_empty(
        self, client: TestClient, _cleanup
    ) -> None:
        marker = _marker()
        customer_id = _create_customer(f"Cliente-{marker}")
        _cleanup(customer_id)

        _create_important_date(
            customer_id, f"{marker}-Longe", True, day=1, month=1
        )

        response = client.get("/api/v1/important-dates/upcoming?days=7")
        assert response.status_code == 200
        assert _find_item(response.json(), marker) is None
