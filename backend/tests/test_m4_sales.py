from __future__ import annotations

from collections.abc import Callable, Iterator
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.customers.models import Customer
from app.products.models import BaseUnit, InventoryMovement, Product
from app.baskets.models import BasketTemplate, BasketTemplateItem
from app.sales.models import (
    Sale,
    SaleBasket,
    SaleBasketItem,
    SaleCompositionHistory,
    SaleDeliveryHistory,
    SaleReopenHistory,
    SaleStatus,
    SaleStockReservation,
    SaleCancellationInspection,
)
from app.payments.models import Payment
from app.inventory.models import StockBatch


@pytest.fixture
def register_sales_cleanup() -> Iterator[Callable[[int], None]]:
    sale_ids: list[int] = []

    def register(sale_id: int) -> None:
        sale_ids.append(sale_id)

    yield register

    with SessionLocal() as db:
        # Clean up dependent tables first (RESTRICT FKs)
        from app.payments.models import Payment
        for sid in sale_ids:
            db.query(Payment).filter(Payment.sale_id == sid).delete(synchronize_session=False)
        db.query(SaleCancellationInspection).filter(
            SaleCancellationInspection.sale_id.in_(sale_ids)
        ).delete(synchronize_session=False)
        db.query(SaleStockReservation).filter(
            SaleStockReservation.sale_id.in_(sale_ids)
        ).delete(synchronize_session=False)
        db.query(InventoryMovement).filter(
            InventoryMovement.sale_id.in_(sale_ids)
        ).delete(synchronize_session=False)
        db.query(Sale).filter(Sale.id.in_(sale_ids)).delete(synchronize_session=False)
        db.commit()


@pytest.fixture
def sample_customer_and_template(
    client: TestClient,
) -> Iterator[tuple[dict, dict, dict]]:
    """Creates a customer, two products, and a basket template with price."""
    suffix = uuid4().hex[:8]
    # 1. Active Customer
    cust_res = client.post(
        "/api/v1/customers",
        json={"name": f"Cliente {suffix}", "phone": f"119{suffix[:8]}"},
    )
    assert cust_res.status_code == 201, cust_res.text
    customer = cust_res.json()

    # 2. Products
    p1_res = client.post("/api/v1/products", json={"name": f"P1 {suffix}", "base_unit": "UN"})
    assert p1_res.status_code == 201, p1_res.text
    p1 = p1_res.json()

    p2_res = client.post("/api/v1/products", json={"name": f"P2 {suffix}", "base_unit": "KG"})
    assert p2_res.status_code == 201, p2_res.text
    p2 = p2_res.json()

    # 3. Basket Template with price
    tpl_res = client.post(
        "/api/v1/basket-templates",
        json={
            "name": f"Cesta Café {suffix}",
            "price": "150.00",
            "items": [
                {"product_id": p1["id"], "quantity": "2"},
                {"product_id": p2["id"], "quantity": "1.5"},
            ],
        },
    )
    assert tpl_res.status_code == 201, tpl_res.text
    template = tpl_res.json()

    # Add stock for products so confirmation works
    client.post(
        f"/api/v1/products/{p1['id']}/inventory/entries",
        json={"quantity": "100"},
    )
    client.post(
        f"/api/v1/products/{p2['id']}/inventory/entries",
        json={"quantity": "100"},
    )

    yield customer, template, {"p1": p1, "p2": p2}

    # Cleanup
    with SessionLocal() as db:
        db.query(StockBatch).filter(
            StockBatch.product_id.in_([p1["id"], p2["id"]])
        ).delete(synchronize_session=False)
        db.query(InventoryMovement).filter(
            InventoryMovement.product_id.in_([p1["id"], p2["id"]])
        ).delete(synchronize_session=False)
        db.query(BasketTemplateItem).filter(BasketTemplateItem.template_id == template["id"]).delete(synchronize_session=False)
        db.query(BasketTemplate).filter(BasketTemplate.id == template["id"]).delete(synchronize_session=False)
        db.query(Customer).filter(Customer.id == customer["id"]).delete(synchronize_session=False)
        db.query(Product).filter(Product.id.in_([p1["id"], p2["id"]])).delete(synchronize_session=False)
        db.commit()


def test_create_sale_requires_active_customer_and_at_least_one_basket(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    customer, template, _ = sample_customer_and_template

    # 1. AC-M4-046: Reject sale without baskets
    res_no_baskets = client.post(
        "/api/v1/sales",
        json={"customer_id": customer["id"], "baskets": []},
    )
    assert res_no_baskets.status_code in (409, 422)

    # 2. AC-M4-007: Reject sale with inactive customer
    client.patch(f"/api/v1/customers/{customer['id']}/status", json={"status": "INACTIVE"})
    res_inactive = client.post(
        "/api/v1/sales",
        json={"customer_id": customer["id"], "baskets": [{"template_id": template["id"]}]},
    )
    assert res_inactive.status_code == 409
    assert "Apenas clientes ativos podem originar novas vendas" in res_inactive.json()["detail"]

    # Reactivate customer and create sale
    client.patch(f"/api/v1/customers/{customer['id']}/status", json={"status": "ACTIVE"})
    res_ok = client.post(
        "/api/v1/sales",
        json={"customer_id": customer["id"], "baskets": [{"template_id": template["id"]}]},
    )
    assert res_ok.status_code == 201
    sale = res_ok.json()
    register_sales_cleanup(sale["id"])

    assert sale["status"] == "RASCUNHO"
    assert sale["customer_id"] == customer["id"]
    assert len(sale["baskets"]) == 1
    assert sale["total"] == "150.00"
    basket = sale["baskets"][0]
    assert basket["name"] == template["name"]
    assert basket["price"] == "150.00"
    assert len(basket["items"]) == 2


def test_reject_template_without_price_and_preserve_snapshot_price(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    customer, template, _ = sample_customer_and_template

    # Create template without price
    tpl_no_price = client.post(
        "/api/v1/basket-templates",
        json={"name": f"Sem Preço {uuid4().hex[:6]}", "price": None, "items": []},
    ).json()

    # AC-M4-004a: Cannot add template without price
    res_blocked = client.post(
        "/api/v1/sales",
        json={"customer_id": customer["id"], "baskets": [{"template_id": tpl_no_price["id"]}]},
    )
    assert res_blocked.status_code == 409
    assert "não possui preço de venda definido" in res_blocked.json()["detail"]

    # AC-M4-004b: Snapshot historical price - template price change does not alter sale basket price
    sale_res = client.post(
        "/api/v1/sales",
        json={"customer_id": customer["id"], "baskets": [{"template_id": template["id"]}]},
    )
    assert sale_res.status_code == 201
    sale = sale_res.json()
    register_sales_cleanup(sale["id"])
    assert sale["baskets"][0]["price"] == "150.00"

    # Update template price in M2
    client.put(
        f"/api/v1/basket-templates/{template['id']}",
        json={"name": template["name"], "price": "299.99"},
    )
    # Check sale again
    refreshed = client.get(f"/api/v1/sales/{sale['id']}").json()
    assert refreshed["baskets"][0]["price"] == "150.00"
    assert refreshed["total"] == "150.00"


def test_multiple_baskets_and_independent_delivery_and_price_in_draft(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    customer, template, _ = sample_customer_and_template

    # AC-M4-001 & AC-M4-002: Multiple baskets from same template
    sale_res = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [
                {
                    "template_id": template["id"],
                    "recipient_name": "Ana",
                    "delivery_address": "Rua 1",
                    "delivery_date": "2026-12-25",
                    "delivery_time": "10:00",
                },
                {
                    "template_id": template["id"],
                    "recipient_name": "Bruno",
                    "delivery_address": "Rua 2",
                    "delivery_date": "2026-12-25",
                    "delivery_time": "15:00",
                },
            ],
        },
    )
    assert sale_res.status_code == 201
    sale = sale_res.json()
    register_sales_cleanup(sale["id"])
    assert len(sale["baskets"]) == 2
    assert sale["total"] == "300.00"

    b1, b2 = sale["baskets"][0], sale["baskets"][1]
    assert b1["recipient_name"] == "Ana"
    assert b2["recipient_name"] == "Bruno"

    # AC-M4-012: Manual price adjustment in RASCUNHO recalculates total
    price_res = client.put(
        f"/api/v1/sales/{sale['id']}/baskets/{b1['id']}/price",
        json={"price": "175.50"},
    )
    assert price_res.status_code == 200
    assert price_res.json()["price"] == "175.50"

    refreshed = client.get(f"/api/v1/sales/{sale['id']}").json()
    assert refreshed["total"] == "325.50"


def test_confirmation_requires_complete_delivery_data(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    customer, template, _ = sample_customer_and_template

    # Create draft with incomplete delivery data (AC-M4-008: allowed in RASCUNHO)
    sale_res = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [{"template_id": template["id"]}],
        },
    )
    assert sale_res.status_code == 201
    sale = sale_res.json()
    register_sales_cleanup(sale["id"])
    b_id = sale["baskets"][0]["id"]

    # AC-M4-009: Attempt to confirm without complete delivery data fails
    confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
    assert confirm_res.status_code == 409
    assert "destinatário, endereço, data e horário" in confirm_res.json()["detail"]

    # Fill delivery data
    client.patch(
        f"/api/v1/sales/{sale['id']}/baskets/{b_id}/delivery",
        json={
            "recipient_name": "Carlos",
            "delivery_address": "Av. Brasil, 100",
            "delivery_date": "2026-10-15",
            "delivery_time": "14:00",
        },
    )

    # Record payment (≥ 50% required for confirmation)
    payment_res = client.post(
        f"/api/v1/sales/{sale['id']}/payments",
        json={
            "amount": "100.00",
            "method": "PIX",
            "idempotency_key": str(uuid4()),
        },
    )
    assert payment_res.status_code == 201

    # Now confirmation succeeds
    confirmed_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
    assert confirmed_res.status_code == 200
    assert confirmed_res.json()["status"] == "CONFIRMADA"

    # AC-M4-013: Price adjustment blocked after confirmation
    blocked_price = client.put(
        f"/api/v1/sales/{sale['id']}/baskets/{b_id}/price",
        json={"price": "200.00"},
    )
    assert blocked_price.status_code == 409
    assert "não pode ser alterado após a confirmação" in blocked_price.json()["detail"]


def test_composition_change_audit_and_preparation_flow(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    customer, template, products = sample_customer_and_template
    p1, p2 = products["p1"], products["p2"]

    sale = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [
                {
                    "template_id": template["id"],
                    "recipient_name": "Carla",
                    "delivery_address": "Rua Flor, 10",
                    "delivery_date": "2026-11-01",
                    "delivery_time": "09:00",
                },
                {
                    "template_id": template["id"],
                    "recipient_name": "Daniel",
                    "delivery_address": "Rua Sol, 20",
                    "delivery_date": "2026-11-01",
                    "delivery_time": "11:00",
                },
            ],
        },
    ).json()
    register_sales_cleanup(sale["id"])
    b1_id = sale["baskets"][0]["id"]
    b2_id = sale["baskets"][1]["id"]

    # Record payment and confirm sale
    client.post(
        f"/api/v1/sales/{sale['id']}/payments",
        json={
            "amount": "200.00",
            "method": "PIX",
            "idempotency_key": str(uuid4()),
        },
    )
    client.post(f"/api/v1/sales/{sale['id']}/confirm")

    # AC-M4-024, AC-M4-047, AC-M4-048: Composition change in CONFIRMADA requires operator name
    no_op = client.put(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/composition",
        json={"items": [{"product_id": p1["id"], "quantity": "3"}], "operator_name": "  "},
    )
    assert no_op.status_code == 409
    assert "operador" in no_op.json()["detail"]

    # Valid composition edit in CONFIRMADA
    valid_edit = client.put(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/composition",
        json={
            "items": [{"product_id": p1["id"], "quantity": "3"}],
            "operator_name": "Mariana Operadora",
        },
    )
    assert valid_edit.status_code == 200
    b1_updated = valid_edit.json()
    assert len(b1_updated["composition_histories"]) == 1
    assert b1_updated["composition_histories"][0]["operator_name"] == "Mariana Operadora"
    assert b1_updated["price"] == "150.00"  # AC-M4-006: Price untouched

    # AC-M4-020: Explicit start of preparation
    prep_res = client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
    assert prep_res.status_code == 200
    assert prep_res.json()["status"] == "EM PREPARAÇÃO"

    # Mark b2 as prepared (AC-M4-031)
    client.post(f"/api/v1/sales/{sale['id']}/baskets/{b2_id}/prepare")
    refreshed = client.get(f"/api/v1/sales/{sale['id']}").json()
    assert refreshed["status"] == "EM PREPARAÇÃO"  # not PRONTA yet because b1 is not prepared (AC-M4-021)
    assert refreshed["baskets"][1]["is_prepared"] is True

    # Mark b1 as prepared
    client.post(f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/prepare")
    refreshed = client.get(f"/api/v1/sales/{sale['id']}").json()
    assert refreshed["status"] == "PRONTA"  # All prepared -> PRONTA!

    # AC-M4-028: Direct composition edit in PRONTA is blocked
    pronta_edit = client.put(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/composition",
        json={
            "items": [{"product_id": p1["id"], "quantity": "1"}],
            "operator_name": "Mariana",
            "confirmed_warning": True,
        },
    )
    assert pronta_edit.status_code == 409
    assert "reabrir a venda" in pronta_edit.json()["detail"]

    # AC-M4-032: Reopen sale from PRONTA with reason and operator
    reopen_no_reason = client.post(
        f"/api/v1/sales/{sale['id']}/reopen",
        json={"reason": "   ", "operator_name": "Mariana"},
    )
    assert reopen_no_reason.status_code == 422 or reopen_no_reason.status_code == 409

    reopened = client.post(
        f"/api/v1/sales/{sale['id']}/reopen",
        json={"reason": "Cliente pediu troca de item", "operator_name": "Mariana"},
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "EM PREPARAÇÃO"
    assert len(reopened.json()["reopen_histories"]) == 1

    # Edit b1 composition in EM PREPARAÇÃO (AC-M4-025 & AC-M4-026 & AC-M4-027)
    # Without warning confirmation -> blocked
    no_confirm = client.put(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/composition",
        json={
            "items": [{"product_id": p1["id"], "quantity": "4"}],
            "operator_name": "Mariana",
            "confirmed_warning": False,
        },
    )
    assert no_confirm.status_code == 409

    # With warning confirmation -> invalidates b1 preparation, preserves b2
    confirmed_change = client.put(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/composition",
        json={
            "items": [{"product_id": p1["id"], "quantity": "4"}],
            "operator_name": "Mariana",
            "confirmed_warning": True,
        },
    )
    assert confirmed_change.status_code == 200
    refreshed_reopened = client.get(f"/api/v1/sales/{sale['id']}").json()
    b1_r = next(b for b in refreshed_reopened["baskets"] if b["id"] == b1_id)
    b2_r = next(b for b in refreshed_reopened["baskets"] if b["id"] == b2_id)
    assert b1_r["is_prepared"] is False  # Invalidated!
    assert b2_r["is_prepared"] is True   # Preserved!

    # Re-prepare b1 -> sale becomes PRONTA again (AC-M4-035)
    client.post(f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/prepare")
    assert client.get(f"/api/v1/sales/{sale['id']}").json()["status"] == "PRONTA"


def test_delivery_flow_and_cancellation_rules(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    customer, template, _ = sample_customer_and_template

    sale = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [
                {
                    "template_id": template["id"],
                    "recipient_name": "Eduardo",
                    "delivery_address": "Rua A",
                    "delivery_date": "2026-11-10",
                    "delivery_time": "14:00",
                },
                {
                    "template_id": template["id"],
                    "recipient_name": "Fernanda",
                    "delivery_address": "Rua B",
                    "delivery_date": "2026-11-10",
                    "delivery_time": "16:00",
                },
            ],
        },
    ).json()
    register_sales_cleanup(sale["id"])
    b1_id = sale["baskets"][0]["id"]
    b2_id = sale["baskets"][1]["id"]

    # Record payment and confirm
    client.post(
        f"/api/v1/sales/{sale['id']}/payments",
        json={
            "amount": "300.00",
            "method": "PIX",
            "idempotency_key": str(uuid4()),
        },
    )
    client.post(f"/api/v1/sales/{sale['id']}/confirm")
    client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
    client.post(f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/prepare")
    client.post(f"/api/v1/sales/{sale['id']}/baskets/{b2_id}/prepare")

    # AC-M4-043: Prepared baskets do not block cancellation before any delivery
    # Let's test cancelling another sale with prepared baskets first:
    test_cancel_sale = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [
                {
                    "template_id": template["id"],
                    "recipient_name": "Gabi",
                    "delivery_address": "Rua C",
                    "delivery_date": "2026-11-12",
                    "delivery_time": "12:00",
                }
            ],
        },
    ).json()
    register_sales_cleanup(test_cancel_sale["id"])
    client.post(
        f"/api/v1/sales/{test_cancel_sale['id']}/payments",
        json={
            "amount": "100.00",
            "method": "PIX",
            "idempotency_key": str(uuid4()),
        },
    )
    client.post(f"/api/v1/sales/{test_cancel_sale['id']}/confirm")
    client.post(f"/api/v1/sales/{test_cancel_sale['id']}/start-preparation")
    client.post(f"/api/v1/sales/{test_cancel_sale['id']}/baskets/{test_cancel_sale['baskets'][0]['id']}/prepare")
    # Cancel allowed (AC-M4-041, AC-M4-043)
    cancel_res = client.post(f"/api/v1/sales/{test_cancel_sale['id']}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELADA"

    # Now in original sale: deliver first basket (AC-M4-037 & AC-M4-039)
    # Delivery requires operator name
    no_op = client.post(f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/deliver", json={"operator_name": " "})
    assert no_op.status_code in (409, 422)

    deliv_res = client.post(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/deliver",
        json={"operator_name": "Entregador Pedro"},
    )
    assert deliv_res.status_code == 200
    b1_delivered = deliv_res.json()
    assert b1_delivered["is_delivered"] is True
    assert len(b1_delivered["delivery_histories"]) == 1
    assert b1_delivered["delivery_histories"][0]["operator_name"] == "Entregador Pedro"

    # AC-M4-023: Sale is not ENTREGUE yet because b2 is still pending
    assert client.get(f"/api/v1/sales/{sale['id']}").json()["status"] != "ENTREGUE"

    # AC-M4-042: Partial delivery blocks cancellation
    cancel_blocked = client.post(f"/api/v1/sales/{sale['id']}/cancel")
    assert cancel_blocked.status_code == 409
    assert "entregas já realizadas" in cancel_blocked.json()["detail"]

    # Deliver second basket -> sale automatically becomes ENTREGUE (AC-M4-023)
    client.post(
        f"/api/v1/sales/{sale['id']}/baskets/{b2_id}/deliver",
        json={"operator_name": "Entregador Pedro"},
    )
    final_sale = client.get(f"/api/v1/sales/{sale['id']}").json()
    assert final_sale["status"] == "ENTREGUE"

    # AC-M4-045: ENTREGUE cannot be cancelled
    cancel_entregue = client.post(f"/api/v1/sales/{sale['id']}/cancel")
    assert cancel_entregue.status_code == 409


def test_deliver_unprepared_basket_is_rejected(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    """A cesta não preparada não pode ser entregue via API."""
    customer, template, _ = sample_customer_and_template

    sale = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [
                {
                    "template_id": template["id"],
                    "recipient_name": "Helena",
                    "delivery_address": "Rua D",
                    "delivery_date": "2026-11-15",
                    "delivery_time": "10:00",
                }
            ],
        },
    ).json()
    register_sales_cleanup(sale["id"])
    b1_id = sale["baskets"][0]["id"]

    # Record payment, confirm, and start preparation
    client.post(
        f"/api/v1/sales/{sale['id']}/payments",
        json={
            "amount": "150.00",
            "method": "PIX",
            "idempotency_key": str(uuid4()),
        },
    )
    confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
    assert confirm_res.status_code == 200, f"Confirm failed: {confirm_res.text}"
    prep_res = client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
    assert prep_res.status_code == 200, f"Start prep failed: {prep_res.text}"

    # Do NOT prepare the basket — attempt delivery directly
    deliver_res = client.post(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/deliver",
        json={"operator_name": "Entregador Teste"},
    )
    assert deliver_res.status_code == 409
    assert "não foi preparada" in deliver_res.json()["detail"]

    # Verify basket is still not delivered
    sale_data = client.get(f"/api/v1/sales/{sale['id']}").json()
    b1 = next(b for b in sale_data["baskets"] if b["id"] == b1_id)
    assert b1["is_delivered"] is False
    assert b1["is_prepared"] is False


def test_deliver_prepared_basket_succeeds(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    """Uma cesta preparada pode ser entregue e a venda é concluída quando todas são entregues."""
    customer, template, _ = sample_customer_and_template

    sale = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [
                {
                    "template_id": template["id"],
                    "recipient_name": "Irene",
                    "delivery_address": "Rua E",
                    "delivery_date": "2026-11-15",
                    "delivery_time": "11:00",
                }
            ],
        },
    ).json()
    register_sales_cleanup(sale["id"])
    b1_id = sale["baskets"][0]["id"]

    # Record payment, confirm, start preparation, and prepare the basket
    client.post(
        f"/api/v1/sales/{sale['id']}/payments",
        json={
            "amount": "150.00",
            "method": "PIX",
            "idempotency_key": str(uuid4()),
        },
    )
    confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
    assert confirm_res.status_code == 200, f"Confirm failed: {confirm_res.text}"
    prep_res = client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
    assert prep_res.status_code == 200, f"Start prep failed: {prep_res.text}"
    prepare_res = client.post(f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/prepare")
    assert prepare_res.status_code == 200, f"Prepare failed: {prepare_res.text}"

    # Deliver the prepared basket
    deliver_res = client.post(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/deliver",
        json={"operator_name": "Entregador Teste"},
    )
    assert deliver_res.status_code == 200, f"Deliver failed: {deliver_res.text}"
    assert deliver_res.json()["is_delivered"] is True
    assert len(deliver_res.json()["delivery_histories"]) == 1
    assert deliver_res.json()["delivery_histories"][0]["operator_name"] == "Entregador Teste"

    # Sale should be ENTREGUE since all baskets are delivered
    sale_data = client.get(f"/api/v1/sales/{sale['id']}").json()
    assert sale_data["status"] == "ENTREGUE"


def test_deliver_already_delivered_basket_is_idempotent(
    client: TestClient,
    sample_customer_and_template: tuple[dict, dict, dict],
    register_sales_cleanup: Callable[[int], None],
) -> None:
    """Entregar uma cesta já entregue retorna sem criar histórico duplicado."""
    customer, template, _ = sample_customer_and_template

    sale = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "baskets": [
                {
                    "template_id": template["id"],
                    "recipient_name": "Joana",
                    "delivery_address": "Rua F",
                    "delivery_date": "2026-11-15",
                    "delivery_time": "12:00",
                }
            ],
        },
    ).json()
    register_sales_cleanup(sale["id"])
    b1_id = sale["baskets"][0]["id"]

    # Record payment, confirm, start preparation, prepare, and deliver
    client.post(
        f"/api/v1/sales/{sale['id']}/payments",
        json={
            "amount": "150.00",
            "method": "PIX",
            "idempotency_key": str(uuid4()),
        },
    )
    confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
    assert confirm_res.status_code == 200, f"Confirm failed: {confirm_res.text}"
    prep_res = client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
    assert prep_res.status_code == 200, f"Start prep failed: {prep_res.text}"
    prepare_res = client.post(f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/prepare")
    assert prepare_res.status_code == 200, f"Prepare failed: {prepare_res.text}"
    deliver_res = client.post(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/deliver",
        json={"operator_name": "Entregador Teste"},
    )
    assert deliver_res.status_code == 200, f"Deliver failed: {deliver_res.text}"

    # Deliver again — should be idempotent
    deliver_again = client.post(
        f"/api/v1/sales/{sale['id']}/baskets/{b1_id}/deliver",
        json={"operator_name": "Entregador Teste 2"},
    )
    assert deliver_again.status_code == 200

    # Should still have only 1 delivery history
    sale_data = client.get(f"/api/v1/sales/{sale['id']}").json()
    b1 = next(b for b in sale_data["baskets"] if b["id"] == b1_id)
    assert len(b1["delivery_histories"]) == 1
    assert b1["delivery_histories"][0]["operator_name"] == "Entregador Teste"
