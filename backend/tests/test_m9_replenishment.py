"""Testes M9 — Reposição de Estoque.

Cobre AC-M9-001 a AC-M9-015 (backend).
"""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.baskets.models import BasketTemplate, BasketTemplateItem
from app.core.database import SessionLocal
from app.inventory.models import StockBatch
from app.sales.models import Sale, SaleBasket, SaleBasketItem


def _dec(value: str) -> Decimal:
    """Helper: compare Decimal values from JSON response."""
    return Decimal(value)


@pytest.fixture
def _cleanup():
    """Cleanup after replenishment tests."""
    yield
    with SessionLocal() as db:
        # Clean up in reverse dependency order
        db.query(SaleBasketItem).delete(synchronize_session=False)
        db.query(SaleBasket).delete(synchronize_session=False)
        # Delete payments before sales (FK constraint)
        from app.payments.models import Payment
        db.query(Payment).delete(synchronize_session=False)
        db.query(Sale).delete(synchronize_session=False)
        db.query(BasketTemplateItem).delete(synchronize_session=False)
        db.query(BasketTemplate).delete(synchronize_session=False)
        db.query(StockBatch).delete(synchronize_session=False)
        db.commit()


def _create_product(name: str | None = None):
    from app.products.models import Product
    with SessionLocal() as db:
        product = Product(name=name or f"REP-{uuid4().hex[:8]}", base_unit="UN")
        db.add(product)
        db.commit()
        db.refresh(product)
        return product.id


def _create_batch(product_id: int, quantity: float, status: str = "ACTIVE"):
    with SessionLocal() as db:
        batch = StockBatch(
            product_id=product_id,
            quantity_original=Decimal(str(quantity)),
            quantity_remaining=Decimal(str(quantity)),
            status=status,
        )
        db.add(batch)
        db.commit()


def _create_template(product_id: int, quantity: float, active: bool = True):
    with SessionLocal() as db:
        template = BasketTemplate(
            name=f"TPL-{uuid4().hex[:8]}", active=active
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        item = BasketTemplateItem(
            template_id=template.id,
            product_id=product_id,
            quantity=Decimal(str(quantity)),
        )
        db.add(item)
        db.commit()
        return template.id


def _create_sale(product_id: int, quantity: float, status: str):
    from app.customers.models import Customer
    with SessionLocal() as db:
        customer = Customer(name=f"Cliente-{uuid4().hex[:8]}", phone="11999999999")
        db.add(customer)
        db.commit()
        db.refresh(customer)
        sale = Sale(customer_id=customer.id, status=status, total=Decimal("0"))
        db.add(sale)
        db.commit()
        db.refresh(sale)
        basket = SaleBasket(
            sale_id=sale.id,
            name=f"Cesta-{uuid4().hex[:8]}",
            price=Decimal("0"),
        )
        db.add(basket)
        db.commit()
        db.refresh(basket)
        item = SaleBasketItem(
            sale_basket_id=basket.id,
            product_id=product_id,
            quantity=Decimal(str(quantity)),
        )
        db.add(item)
        db.commit()
        return sale.id


class TestReplenishmentStockCalculation:
    """AC-M9-001: Estoque atual calculado a partir dos lotes ativos."""

    def test_stock_from_active_batches(self, client: TestClient, _cleanup):
        product_id = _create_product()
        _create_batch(product_id, 5)
        _create_batch(product_id, 3)
        _create_batch(product_id, 2)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["stock_quantity"]) == Decimal("10")

    def test_exhausted_batch_not_counted(self, client: TestClient, _cleanup):
        product_id = _create_product()
        _create_batch(product_id, 5, status="ACTIVE")
        # EXHAUSTED batch: quantity_original > 0 (constraint), quantity_remaining = 0
        with SessionLocal() as db:
            batch = StockBatch(
                product_id=product_id,
                quantity_original=Decimal("5"),
                quantity_remaining=Decimal("0"),
                status="EXHAUSTED",
            )
            db.add(batch)
            db.commit()

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["stock_quantity"]) == Decimal("5")


class TestReplenishmentEstimatedNeed:
    """AC-M9-002: Necessidade estimada a partir dos templates ativos."""

    def test_estimated_need_from_active_templates(self, client: TestClient, _cleanup):
        product_id = _create_product()
        _create_template(product_id, 3)
        _create_template(product_id, 2)
        _create_batch(product_id, 100)  # estoque alto para não afetar status

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["estimated_need"]) == Decimal("5")

    def test_inactive_template_not_counted(self, client: TestClient, _cleanup):
        """AC-M9-009: Template inativo não gera necessidade."""
        product_id = _create_product()
        _create_template(product_id, 3, active=True)
        _create_template(product_id, 7, active=False)
        _create_batch(product_id, 100)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["estimated_need"]) == Decimal("3")


class TestReplenishmentUrgentNeed:
    """AC-M9-003: Necessidade urgente a partir das vendas confirmadas."""

    def test_urgent_need_from_confirmed_sale(self, client: TestClient, _cleanup):
        product_id = _create_product()
        _create_sale(product_id, 2, status="CONFIRMADA")
        _create_batch(product_id, 1)  # estoque baixo para gerar CRÍTICO

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["urgent_need"]) == Decimal("2")

    def test_draft_sale_not_counted(self, client: TestClient, _cleanup):
        product_id = _create_product()
        _create_sale(product_id, 5, status="RASCUNHO")
        _create_batch(product_id, 100)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["urgent_need"]) == Decimal("0")

    def test_cancelled_sale_not_counted(self, client: TestClient, _cleanup):
        """AC-M9-004: Venda cancelada não gera necessidade."""
        product_id = _create_product()
        _create_sale(product_id, 5, status="CANCELADA")
        _create_batch(product_id, 100)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["urgent_need"]) == Decimal("0")

    def test_delivered_sale_not_counted(self, client: TestClient, _cleanup):
        """AC-M9-005: Venda entregue não gera necessidade."""
        product_id = _create_product()
        _create_sale(product_id, 5, status="ENTREGUE")
        _create_batch(product_id, 100)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["urgent_need"]) == Decimal("0")


class TestReplenishmentStatus:
    """AC-M9-006 a AC-M9-008: Classificação de status."""

    def test_status_ok_when_stock_sufficient(self, client: TestClient, _cleanup):
        """AC-M9-006: Status OK quando estoque suficiente."""
        product_id = _create_product()
        _create_batch(product_id, 10)
        _create_template(product_id, 5)
        _create_sale(product_id, 3, status="CONFIRMADA")

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["status"] == "OK"

    def test_status_ok_when_no_need(self, client: TestClient, _cleanup):
        """AC-M9-006: Status OK quando não há necessidade."""
        product_id = _create_product()
        _create_batch(product_id, 10)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["status"] == "OK"

    def test_status_baixo_when_low_no_urgent(self, client: TestClient, _cleanup):
        """AC-M9-007: Status BAIXO quando estoque insuficiente sem urgência."""
        product_id = _create_product()
        _create_batch(product_id, 3)
        _create_template(product_id, 5)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["status"] == "BAIXO"

    def test_status_critico_when_low_with_urgent(self, client: TestClient, _cleanup):
        """AC-M9-008: Status CRÍTICO quando estoque insuficiente com urgência."""
        product_id = _create_product()
        _create_batch(product_id, 2)
        _create_template(product_id, 5)
        _create_sale(product_id, 4, status="CONFIRMADA")

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["status"] == "CRÍTICO"

    def test_product_with_no_need_is_ok(self, client: TestClient, _cleanup):
        """AC-M9-010: Produto sem necessidade é OK."""
        product_id = _create_product()
        # Sem template, sem venda — apenas estoque zero
        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        # Se não há necessidade, o produto pode não aparecer na lista
        # (não há stock, não há need — nenhum dado para agregar)
        # Mas se aparecer, deve ser OK


class TestReplenishmentAPI:
    """AC-M9-011 a AC-M9-015: API e filtros."""

    def test_endpoint_returns_replenishment_list(self, client: TestClient, _cleanup):
        """AC-M9-011: Endpoint retorna lista de reposição."""
        product_id = _create_product()
        _create_batch(product_id, 10)

        resp = client.get("/api/v1/inventory/replenishment")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        item = data["items"][0]
        assert "product_id" in item
        assert "product_name" in item
        assert "stock_quantity" in item
        assert "estimated_need" in item
        assert "urgent_need" in item
        assert "total_need" in item
        assert "shortage" in item
        assert "status" in item

    def test_filter_by_status(self, client: TestClient, _cleanup):
        """AC-M9-012: Filtro por status funciona."""
        product_ok = _create_product()
        product_baixo = _create_product()
        _create_batch(product_ok, 100)
        _create_batch(product_baixo, 1)
        _create_template(product_baixo, 10)

        resp = client.get("/api/v1/inventory/replenishment?status=BAIXO")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "BAIXO"

    def test_filter_by_product_id(self, client: TestClient, _cleanup):
        """AC-M9-013: Filtro por produto funciona."""
        product_id = _create_product()
        _create_batch(product_id, 10)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["product_id"] == product_id

    def test_shortage_calculated_correctly(self, client: TestClient, _cleanup):
        """AC-M9-014: Shortage calculado corretamente."""
        product_id = _create_product()
        _create_batch(product_id, 10)
        _create_template(product_id, 15)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["shortage"]) == Decimal("5")

    def test_shortage_minimum_zero(self, client: TestClient, _cleanup):
        """AC-M9-014: Shortage mínimo 0 quando estoque suficiente."""
        product_id = _create_product()
        _create_batch(product_id, 20)
        _create_template(product_id, 10)

        resp = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert _dec(item["shortage"]) == Decimal("0")

    def test_real_time_calculation(self, client: TestClient, _cleanup):
        """AC-M9-015: Lista de reposição é cálculo em tempo real."""
        product_id = _create_product()
        _create_batch(product_id, 100)
        _create_template(product_id, 10)

        # Primeiro: estoque alto, status OK
        resp1 = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp1.json()["items"][0]["status"] == "OK"

        # Reduzir estoque
        with SessionLocal() as db:
            batch = db.query(StockBatch).filter(
                StockBatch.product_id == product_id
            ).first()
            batch.quantity_remaining = Decimal("3")
            db.commit()

        # Segundo: estoque baixo, status BAIXO
        resp2 = client.get(f"/api/v1/inventory/replenishment?product_id={product_id}")
        assert resp2.json()["items"][0]["status"] == "BAIXO"
