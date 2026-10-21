"""M5 Concurrency Integration Tests.

Validates transactional guarantees with real PostgreSQL, independent sessions,
and deterministic synchronization using barriers and SQL event listeners.

Covers:
1. Stock adjustment vs confirmation concurrency
2. Two sales competing for the same stock
3. Payment idempotency — same key, same content (concurrent)
4. Payment idempotency — same key, different content (concurrent)
5. Lock hierarchy and deadlock prevention
6. Concurrent composition edits
7. Cancel after preparation — inspection and reintegration
8. Rollback of preparation start on insufficient stock
"""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from threading import Barrier, Event
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.database import SessionLocal, engine
from app.customers.models import Customer
from app.products.models import BaseUnit, InventoryMovement, Product
from app.baskets.models import BasketTemplate, BasketTemplateItem
from app.sales.models import (
    Sale,
    SaleBasket,
    SaleBasketItem,
    SaleStockReservation,
    SaleCancellationInspection,
)
from app.payments.models import Payment
from app.inventory.models import StockBatch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_product(client: TestClient, name: str) -> dict:
    res = client.post("/api/v1/products", json={"name": name, "base_unit": "UN"})
    assert res.status_code == 201, res.text
    return res.json()


def _add_stock(client: TestClient, product_id: int, quantity: int) -> None:
    res = client.post(
        f"/api/v1/products/{product_id}/inventory/entries",
        json={"quantity": str(quantity)},
    )
    assert res.status_code == 201, res.text


def _get_balance(client: TestClient, product_id: int) -> Decimal:
    res = client.get(f"/api/v1/products/{product_id}/inventory/balance")
    assert res.status_code == 200, res.text
    return Decimal(res.json()["quantity"])


def _create_customer(client: TestClient) -> dict:
    res = client.post(
        "/api/v1/customers",
        json={"name": f"Cliente {uuid4().hex[:8]}", "phone": f"119{uuid4().hex[:8]}"},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _create_template(client: TestClient, product_id: int, quantity: int, price: str) -> dict:
    res = client.post(
        "/api/v1/basket-templates",
        json={
            "name": f"Cesta {uuid4().hex[:8]}",
            "price": price,
            "items": [{"product_id": product_id, "quantity": str(quantity)}],
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def _create_sale(
    client: TestClient,
    customer_id: int,
    template_id: int,
    delivery_data: dict | None = None,
) -> dict:
    baskets = [
        {
            "template_id": template_id,
            "recipient_name": delivery_data.get("recipient_name", "Teste") if delivery_data else None,
            "delivery_address": delivery_data.get("delivery_address", "Rua Teste") if delivery_data else None,
            "delivery_date": delivery_data.get("delivery_date", "2026-12-25") if delivery_data else None,
            "delivery_time": delivery_data.get("delivery_time", "10:00") if delivery_data else None,
        }
    ]
    res = client.post(
        "/api/v1/sales",
        json={"customer_id": customer_id, "baskets": baskets},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _record_payment(client: TestClient, sale_id: int, amount: str, method: str, key: str) -> dict:
    res = client.post(
        f"/api/v1/sales/{sale_id}/payments",
        json={"amount": amount, "method": method, "idempotency_key": key},
    )
    assert res.status_code == 201, res.text
    return res.json()


def _confirm_sale(client: TestClient, sale_id: int) -> int:
    res = client.post(f"/api/v1/sales/{sale_id}/confirm")
    return res.status_code


def _cleanup_test_data(
    product_ids: list[int],
    customer_ids: list[int],
    template_ids: list[int],
    sale_ids: list[int],
) -> None:
    with SessionLocal() as db:
        for sid in sale_ids:
            db.query(Payment).filter(Payment.sale_id == sid).delete(synchronize_session=False)
            db.query(SaleCancellationInspection).filter(
                SaleCancellationInspection.sale_id == sid
            ).delete(synchronize_session=False)
            db.query(SaleStockReservation).filter(
                SaleStockReservation.sale_id == sid
            ).delete(synchronize_session=False)
            db.query(InventoryMovement).filter(
                InventoryMovement.sale_id == sid
            ).delete(synchronize_session=False)
        db.query(Sale).filter(Sale.id.in_(sale_ids)).delete(synchronize_session=False)
        for pid in product_ids:
            db.query(InventoryMovement).filter(
                InventoryMovement.product_id == pid
            ).delete(synchronize_session=False)
        db.query(BasketTemplateItem).filter(
            BasketTemplateItem.template_id.in_(template_ids)
        ).delete(synchronize_session=False)
        db.query(BasketTemplate).filter(
            BasketTemplate.id.in_(template_ids)
        ).delete(synchronize_session=False)
        db.query(StockBatch).filter(
            StockBatch.product_id.in_(product_ids)
        ).delete(synchronize_session=False)
        db.query(Customer).filter(Customer.id.in_(customer_ids)).delete(synchronize_session=False)
        db.query(Product).filter(Product.id.in_(product_ids)).delete(synchronize_session=False)
        db.commit()


# ---------------------------------------------------------------------------
# Test 1: Stock adjustment vs confirmation — concurrent
# ---------------------------------------------------------------------------

def test_adjustment_vs_confirmation_concurrent() -> None:
    """Two concurrent operations: adjustment (-stock) and confirmation (reserve).
    Only one should succeed; stock must never go negative.

    Uses Barrier + before_cursor_execute to synchronize FOR UPDATE locks
    so both transactions hold the product lock simultaneously, then proceed.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Ajuste {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 5)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            template = _create_template(client, product["id"], 5, "100.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            # Record payment >= 50%
            _record_payment(client, sale["id"], "100.00", "PIX", str(uuid4()))

            # Synchronize on the FIRST FOR UPDATE lock only — both threads
            # will wait at the barrier until both have acquired their lock.
            # The adjustment locks the product first; the confirmation locks
            # the sale first, then the product. We synchronize on the product
            # lock to ensure both are waiting.
            product_lock_barrier = Barrier(2)
            product_lock_count = [0]

            def synchronize_product_locks(_conn: Any, _cursor: Any, statement: str, *_args: Any) -> None:
                upper = statement.upper()
                if "FOR UPDATE" in upper and "PRODUCTS" in upper:
                    product_lock_count[0] += 1
                    product_lock_barrier.wait(timeout=10)

            def do_adjustment() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    res = c.post(
                        f"/api/v1/products/{product['id']}/inventory/adjustments",
                        json={"quantity": "-5"},
                    )
                    return res.status_code

            def do_confirm() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    return _confirm_sale(c, sale["id"])

            event.listen(engine, "before_cursor_execute", synchronize_product_locks)
            try:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [
                        executor.submit(do_adjustment),
                        executor.submit(do_confirm),
                    ]
                    statuses = [f.result(timeout=30) for f in futures]
            finally:
                event.remove(engine, "before_cursor_execute", synchronize_product_locks)

            # Both threads hit the product lock barrier, so they're synchronized.
            # One will succeed (201 for adjustment or 200 for confirm),
            # the other will fail (409) because stock/reservation is consumed.
            assert len(statuses) == 2
            success_count = statuses.count(201) + statuses.count(200)
            assert success_count == 1, f"Expected 1 success, got {success_count}: {statuses}"

            # Stock must never be negative
            balance = _get_balance(client, product["id"])
            assert balance >= 0

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 2: Two sales competing for the same stock
# ---------------------------------------------------------------------------

def test_two_sales_competing_for_stock() -> None:
    """Two confirmations for different sales, same product, insufficient stock for both.
    Only one should succeed.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Competicao {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 5)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            template = _create_template(client, product["id"], 5, "100.00")
            template_ids.append(template["id"])

            # Create two sales
            sale1 = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale1["id"])
            _record_payment(client, sale1["id"], "100.00", "PIX", str(uuid4()))

            sale2 = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Bruno", "delivery_address": "Rua 2", "delivery_date": "2026-12-25", "delivery_time": "11:00"},
            )
            sale_ids.append(sale2["id"])
            _record_payment(client, sale2["id"], "100.00", "PIX", str(uuid4()))

            lock_barrier = Barrier(2)
            lock_count = [0]

            def synchronize_locks(_conn: Any, _cursor: Any, statement: str, *_args: Any) -> None:
                if "FOR UPDATE" in statement.upper():
                    lock_count[0] += 1
                    lock_barrier.wait(timeout=10)

            def confirm1() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    return _confirm_sale(c, sale1["id"])

            def confirm2() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    return _confirm_sale(c, sale2["id"])

            event.listen(engine, "before_cursor_execute", synchronize_locks)
            try:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [executor.submit(confirm1), executor.submit(confirm2)]
                    statuses = [f.result(timeout=30) for f in futures]
            finally:
                event.remove(engine, "before_cursor_execute", synchronize_locks)

            # Exactly one succeeds
            assert statuses.count(200) == 1
            assert statuses.count(409) == 1

            # Verify only one sale is CONFIRMADA
            with SessionLocal() as db:
                confirmed = db.query(Sale).filter(
                    Sale.id.in_(sale_ids),
                    Sale.status == "CONFIRMADA",
                ).count()
            assert confirmed == 1

            # Verify only one reservation row exists (sale-level, one row per product)
            with SessionLocal() as db:
                reservations = db.query(SaleStockReservation).filter(
                    SaleStockReservation.sale_id.in_(sale_ids),
                    SaleStockReservation.status == "ACTIVE",
                ).count()
            assert reservations == 1  # 1 reservation row for the confirmed sale

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 3: Payment idempotency — same key, same content (concurrent)
# ---------------------------------------------------------------------------

def test_payment_idempotency_same_key_same_content_concurrent() -> None:
    """Two concurrent requests with the same idempotency key and same values.
    Both should succeed (return the same payment), no duplicates.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Idemp {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 100)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            template = _create_template(client, product["id"], 1, "100.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            idempotency_key = str(uuid4())
            results: list[tuple[int, dict | None]] = []

            def do_payment() -> tuple[int, dict | None]:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    res = c.post(
                        f"/api/v1/sales/{sale['id']}/payments",
                        json={
                            "amount": "50.00",
                            "method": "PIX",
                            "idempotency_key": idempotency_key,
                        },
                    )
                    return (res.status_code, res.json() if res.status_code < 400 else None)

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(do_payment), executor.submit(do_payment)]
                for f in as_completed(futures, timeout=30):
                    results.append(f.result())

            # Both should succeed (201 or 200)
            for status, _ in results:
                assert status in (200, 201), f"Unexpected status: {status}"

            # Only one payment record in the database
            with SessionLocal() as db:
                count = db.query(Payment).filter(
                    Payment.sale_id == sale["id"]
                ).count()
            assert count == 1

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 4: Payment idempotency — same key, different content (concurrent)
# ---------------------------------------------------------------------------

def test_payment_idempotency_same_key_different_amount_concurrent() -> None:
    """Two concurrent requests with the same key but different amounts.
    One succeeds, the other gets a conflict (409).
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Idemp2 {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 100)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            template = _create_template(client, product["id"], 1, "100.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            idempotency_key = str(uuid4())
            results: list[int] = []

            def do_payment_50() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    res = c.post(
                        f"/api/v1/sales/{sale['id']}/payments",
                        json={
                            "amount": "50.00",
                            "method": "PIX",
                            "idempotency_key": idempotency_key,
                        },
                    )
                    return res.status_code

            def do_payment_75() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    res = c.post(
                        f"/api/v1/sales/{sale['id']}/payments",
                        json={
                            "amount": "75.00",
                            "method": "PIX",
                            "idempotency_key": idempotency_key,
                        },
                    )
                    return res.status_code

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(do_payment_50), executor.submit(do_payment_75)]
                for f in as_completed(futures, timeout=30):
                    results.append(f.result())

            # One succeeds, one fails with conflict
            assert len(results) == 2
            assert 201 in results or 200 in results
            assert 409 in results

            # Only one payment in DB
            with SessionLocal() as db:
                count = db.query(Payment).filter(
                    Payment.sale_id == sale["id"]
                ).count()
            assert count == 1

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 5: Lock hierarchy — no deadlock under concurrent flows
# ---------------------------------------------------------------------------

def test_lock_hierarchy_no_deadlock() -> None:
    """Concurrent confirmation and preparation start on different sales sharing products.
    Should not deadlock; should complete within timeout.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Lock {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 10)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            template = _create_template(client, product["id"], 3, "100.00")
            template_ids.append(template["id"])

            # Sale 1: will be confirmed
            sale1 = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale1["id"])
            _record_payment(client, sale1["id"], "100.00", "PIX", str(uuid4()))

            # Sale 2: will be confirmed and prepared
            sale2 = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Bruno", "delivery_address": "Rua 2", "delivery_date": "2026-12-25", "delivery_time": "11:00"},
            )
            sale_ids.append(sale2["id"])
            _record_payment(client, sale2["id"], "100.00", "PIX", str(uuid4()))

            completed = [False, False]
            deadlock_detected = [False]

            def confirm_sale1() -> None:
                try:
                    with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                        _confirm_sale(c, sale1["id"])
                    completed[0] = True
                except Exception:
                    deadlock_detected[0] = True

            def confirm_and_prep_sale2() -> None:
                try:
                    with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                        status = _confirm_sale(c, sale2["id"])
                        if status == 200:
                            prep = c.post(f"/api/v1/sales/{sale2['id']}/start-preparation")
                            if prep.status_code != 200:
                                pass  # May fail due to stock — that's OK
                    completed[1] = True
                except Exception:
                    deadlock_detected[1] = True

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(confirm_sale1),
                    executor.submit(confirm_and_prep_sale2),
                ]
                # If deadlock, these will hang. Timeout = 30s.
                for f in as_completed(futures, timeout=30):
                    f.result(timeout=5)

            # No deadlock detected
            assert not any(deadlock_detected), "Deadlock or timeout detected!"
            # At least one operation completed
            assert any(completed), "No operation completed"

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 6: Concurrent composition edits on the same sale
# ---------------------------------------------------------------------------

def test_concurrent_composition_edits() -> None:
    """Two concurrent composition changes on the same sale.
    Serialized by sale lock; no corruption.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            p1 = _create_product(client, f"Produto Comp1 {uuid4().hex[:8]}")
            p2 = _create_product(client, f"Produto Comp2 {uuid4().hex[:8]}")
            product_ids.extend([p1["id"], p2["id"]])
            _add_stock(client, p1["id"], 100)
            _add_stock(client, p2["id"], 100)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            template = _create_template(client, p1["id"], 2, "100.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])
            _record_payment(client, sale["id"], "100.00", "PIX", str(uuid4()))
            confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
            assert confirm_res.status_code == 200

            basket_id = sale["baskets"][0]["id"]
            results: list[int] = []

            def edit_to_p1() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    res = c.put(
                        f"/api/v1/sales/{sale['id']}/baskets/{basket_id}/composition",
                        json={
                            "items": [{"product_id": p1["id"], "quantity": "5"}],
                            "operator_name": "Operador1",
                        },
                    )
                    return res.status_code

            def edit_to_p2() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    res = c.put(
                        f"/api/v1/sales/{sale['id']}/baskets/{basket_id}/composition",
                        json={
                            "items": [{"product_id": p2["id"], "quantity": "3"}],
                            "operator_name": "Operador2",
                        },
                    )
                    return res.status_code

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(edit_to_p1), executor.submit(edit_to_p2)]
                for f in as_completed(futures, timeout=30):
                    results.append(f.result())

            # Both should succeed (serialized, not conflicting on data)
            assert all(s == 200 for s in results), f"Unexpected statuses: {results}"

            # Verify composition is consistent — one of the edits won
            refreshed = client.get(f"/api/v1/sales/{sale['id']}").json()
            basket = refreshed["baskets"][0]
            assert len(basket["items"]) >= 1

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 7: Cancel after preparation — inspection and reintegration
# ---------------------------------------------------------------------------

def test_cancel_after_prep_inspection_reintegration() -> None:
    """Full cycle: confirm → prep → cancel → inspect → reintegrate.
    Verify inspection records, no double reintegration, correct stock.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Cancel {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            initial_stock = 10
            _add_stock(client, product["id"], initial_stock)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            template = _create_template(client, product["id"], 3, "100.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            # Confirm
            _record_payment(client, sale["id"], "100.00", "PIX", str(uuid4()))
            confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
            assert confirm_res.status_code == 200

            # Start preparation — deducts 3 units
            prep_res = client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
            assert prep_res.status_code == 200
            assert prep_res.json()["status"] == "EM PREPARAÇÃO"

            # Stock should be 7 (10 - 3)
            balance_after_prep = _get_balance(client, product["id"])
            assert balance_after_prep == 7

            # Cancel — should create inspection records
            cancel_res = client.post(f"/api/v1/sales/{sale['id']}/cancel")
            assert cancel_res.status_code == 200
            assert cancel_res.json()["status"] == "CANCELADA"

            # Verify inspection record created
            with SessionLocal() as db:
                inspections = db.query(SaleCancellationInspection).filter(
                    SaleCancellationInspection.sale_id == sale["id"]
                ).all()
            assert len(inspections) == 1
            inspection = inspections[0]
            assert inspection.status == "PENDING"
            assert inspection.consumed_quantity == 3

            # Record inspection: 2 reusable out of 3 consumed
            inspect_res = client.post(
                f"/api/v1/sales/{sale['id']}/inspections/{inspection.id}/record",
                json={
                    "inspected_quantity": "3",
                    "reusable_quantity": "2",
                    "operator_name": "Inspector Teste",
                },
            )
            assert inspect_res.status_code == 200, inspect_res.text
            assert inspect_res.json()["status"] == "INSPECTED"

            # Verify inspected_at has timezone info after DB round-trip (UTC semantics)
            with SessionLocal() as db:
                inspection_from_db = db.query(SaleCancellationInspection).filter(
                    SaleCancellationInspection.id == inspection.id
                ).one_or_none()
                assert inspection_from_db is not None
                assert inspection_from_db.inspected_at is not None, (
                    "inspected_at should be set after record_inspection"
                )
                assert inspection_from_db.inspected_at.tzinfo is not None, (
                    "inspected_at must have timezone info (UTC) after DB round-trip"
                )

            # Reintegrate 2 units
            reintegrate_res = client.post(
                f"/api/v1/sales/{sale['id']}/inspections/{inspection.id}/reintegrate",
                json={"quantity": "2", "operator_name": "Inspector Teste"},
            )
            assert reintegrate_res.status_code == 200, reintegrate_res.text
            assert reintegrate_res.json()["status"] == "REINTEGRATED"

            # Stock should be 9 (7 + 2 reintegrated)
            balance_after_reintegrate = _get_balance(client, product["id"])
            assert balance_after_reintegrate == 9

            # Double reintegration should be blocked
            double_res = client.post(
                f"/api/v1/sales/{sale['id']}/inspections/{inspection.id}/reintegrate",
                json={"quantity": "1", "operator_name": "Inspector Teste"},
            )
            assert double_res.status_code == 409

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 8: Rollback of preparation start on insufficient stock
# ---------------------------------------------------------------------------

def test_preparation_start_rollback_on_insufficient_stock() -> None:
    """If preparation start fails due to insufficient stock for one product,
    no partial deduction should occur.

    Note: confirmation succeeds because check_reservable checks availability
    (balance - active_reservations). With 10 p1 and 1 p2, and no other
    reservations, both products are reservable. The preparation start then
    fails because p2 has only 1 unit physically but needs 3.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            p1 = _create_product(client, f"Produto Rollback1 {uuid4().hex[:8]}")
            p2 = _create_product(client, f"Produto Rollback2 {uuid4().hex[:8]}")
            product_ids.extend([p1["id"], p2["id"]])

            # Both products have enough for reservation check
            # (reservation does NOT deduct physical stock)
            _add_stock(client, p1["id"], 10)
            _add_stock(client, p2["id"], 5)  # Enough for reservation (3 needed)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            # Template with both products
            tpl_res = client.post(
                "/api/v1/basket-templates",
                json={
                    "name": f"Cesta Rollback {uuid4().hex[:8]}",
                    "price": "100.00",
                    "items": [
                        {"product_id": p1["id"], "quantity": "2"},
                        {"product_id": p2["id"], "quantity": "3"},
                    ],
                },
            )
            assert tpl_res.status_code == 201
            template = tpl_res.json()
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            _record_payment(client, sale["id"], "100.00", "PIX", str(uuid4()))
            confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
            assert confirm_res.status_code == 200

            # Now reduce p2 stock below what's needed for physical deduction
            # (reservation already exists, so adjustment checks coverage)
            # We need to reduce p2 from 5 to 1, but active reservations = 3
            # So adjustment of -4: resulting_balance = 1, active_res = 3 -> rejected
            # Instead, we use a separate product scenario:
            # Reduce p2 stock to 1 BEFORE confirming a second sale
            # Actually, let's just test: after confirm, reduce stock so prep fails
            # Adjustment -4 on p2: balance 5, active_res 3, resulting 1 < 3 -> rejected
            # So we need to cancel first or use a different approach.
            # Simplest: create the sale with enough stock, confirm, then
            # manually reduce stock via a direct DB operation to simulate
            # stock being consumed by another process.
            # Actually, the cleanest test: confirm succeeds (stock reserved),
            # then we adjust stock down so prep fails.
            # Adjustment of -1 on p2: balance 5, active_res 3, resulting 4 >= 3 -> allowed
            # Then balance = 4. Prep needs 3. 4 >= 3 -> prep succeeds.
            # We need balance < 3 for prep to fail.
            # Adjustment of -2: balance 5, active_res 3, resulting 3 >= 3 -> allowed
            # Then balance = 3. Prep needs 3. 3 >= 3 -> prep succeeds.
            # Adjustment of -3: balance 5, active_res 3, resulting 2 < 3 -> rejected!
            # So we can only adjust -2 max. Balance becomes 3. Prep needs 3. OK.
            # To make prep fail, we need to get balance below 3.
            # The coverage check prevents us from going below active_res (3).
            # Therefore, with the coverage check in place, prep cannot fail
            # due to adjustment alone — the coverage check protects it.
            #
            # The real rollback scenario: two products, one fails during prep.
            # We need p2 to have reserved stock but insufficient physical balance.
            # This can happen if another sale's prep consumed the stock.
            #
            # Revised test: two sales share p2. Sale 1 confirms and preps first,
            # consuming p2 stock. Then sale 2 tries to prep but p2 is exhausted.
            # However, sale 2 confirmation would fail because stock is already reserved.
            #
            # Simplest valid rollback test: confirm succeeds, then we directly
            # manipulate the balance to simulate stock loss, then prep fails.
            # We do this by creating an OUTPUT movement directly (simulating
            # another process consuming the stock).
            #
            # Actually, the simplest approach: use the adjustment to reduce
            # stock to exactly the active reservation level, then create
            # a second reservation that consumes the remaining availability,
            # then try to prep the first sale.
            #
            # Let's simplify: test that prep fails when stock is insufficient
            # by having the confirmation succeed (stock available for reservation)
            # but then another sale consumes the physical stock before prep.
            #
            # Simplest valid test: confirm sale (reserves 3 p2), then
            # create another sale that also reserves p2 and preps first,
            # consuming the physical stock. Then the first sale's prep fails.
            # But the second sale can't confirm because availability = 5 - 3 = 2 < 3.
            #
            # Final approach: just test that prep correctly checks balance
            # and rolls back when balance < to_deduct. We simulate this by
            # having p2 with balance = 2 (below the 3 needed) at prep time.
            # We achieve this by confirming (reserves 3, balance stays 5),
            # then adjusting -3 (balance 5, active_res 3, resulting 2 < 3 -> rejected).
            #
            # The coverage check prevents this. So the rollback scenario
            # can only happen with concurrent operations.
            #
            # For this test, we'll use a direct DB manipulation to set
            # the balance low, simulating a concurrent stock consumer.
            with SessionLocal() as db:
                # Delete one ENTRY movement to reduce balance from 5 to 2
                entry = db.query(InventoryMovement).filter(
                    InventoryMovement.product_id == p2["id"],
                    InventoryMovement.type == "ENTRY",
                ).first()
                if entry:
                    entry.quantity = Decimal("2")
                    db.commit()

            # Now p2 balance = 2, but reservation needs 3 for prep
            prep_res = client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
            assert prep_res.status_code == 409

            # Sale should still be CONFIRMADA
            refreshed = client.get(f"/api/v1/sales/{sale['id']}").json()
            assert refreshed["status"] == "CONFIRMADA"

            # No OUTPUT movements should exist
            with SessionLocal() as db:
                outputs = db.query(InventoryMovement).filter(
                    InventoryMovement.sale_id == sale["id"],
                    InventoryMovement.type == "OUTPUT",
                ).count()
            assert outputs == 0

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 9: AC-M5-003 — Payment methods: only PIX and CARTAO accepted
# ---------------------------------------------------------------------------

def test_payment_methods_only_pix_cartao() -> None:
    """PIX and CARTAO are accepted; DINHEIRO, OUTRO and invalid values are rejected.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Metodo {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 100)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            template = _create_template(client, product["id"], 1, "100.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            # PIX should be accepted
            res = client.post(
                f"/api/v1/sales/{sale['id']}/payments",
                json={"amount": "10.00", "method": "PIX", "idempotency_key": str(uuid4())},
            )
            assert res.status_code == 201, f"PIX should be accepted: {res.text}"

            # CARTAO should be accepted
            res = client.post(
                f"/api/v1/sales/{sale['id']}/payments",
                json={"amount": "10.00", "method": "CARTAO", "idempotency_key": str(uuid4())},
            )
            assert res.status_code == 201, f"CARTAO should be accepted: {res.text}"

            # DINHEIRO should be rejected
            res = client.post(
                f"/api/v1/sales/{sale['id']}/payments",
                json={"amount": "10.00", "method": "DINHEIRO", "idempotency_key": str(uuid4())},
            )
            assert res.status_code == 422, f"DINHEIRO should be rejected: {res.text}"

            # OUTRO should be rejected
            res = client.post(
                f"/api/v1/sales/{sale['id']}/payments",
                json={"amount": "10.00", "method": "OUTRO", "idempotency_key": str(uuid4())},
            )
            assert res.status_code == 422, f"OUTRO should be rejected: {res.text}"

            # Invalid method should be rejected
            res = client.post(
                f"/api/v1/sales/{sale['id']}/payments",
                json={"amount": "10.00", "method": "BOLETO", "idempotency_key": str(uuid4())},
            )
            assert res.status_code == 422, f"BOLETO should be rejected: {res.text}"

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 10: AC-M5-041 — Excess payment is rejected
# ---------------------------------------------------------------------------

def test_payment_excess_rejected() -> None:
    """Sale total R$180.00, already paid R$160.00, remaining R$20.00.
    Attempting to register R$30.00 must be rejected. Balance remains R$160.00.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Excesso {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 100)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            # Template with price R$180.00
            template = _create_template(client, product["id"], 1, "180.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            # Register R$160.00 in two payments
            _record_payment(client, sale["id"], "100.00", "PIX", str(uuid4()))
            _record_payment(client, sale["id"], "60.00", "PIX", str(uuid4()))

            # Verify total paid is R$160.00
            total_res = client.get(f"/api/v1/sales/{sale['id']}/payments/total")
            assert total_res.status_code == 200
            assert Decimal(total_res.json()["total_paid"]) == Decimal("160.00")
            assert Decimal(total_res.json()["sale_total"]) == Decimal("180.00")

            # Attempt to register R$30.00 — should be rejected (160 + 30 = 190 > 180)
            res = client.post(
                f"/api/v1/sales/{sale['id']}/payments",
                json={"amount": "30.00", "method": "PIX", "idempotency_key": str(uuid4())},
            )
            assert res.status_code == 409, f"Excess payment should be rejected: {res.text}"

            # Verify total paid is still R$160.00
            total_res = client.get(f"/api/v1/sales/{sale['id']}/payments/total")
            assert total_res.status_code == 200
            assert Decimal(total_res.json()["total_paid"]) == Decimal("160.00")

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 11: AC-M5-042 — Exact remaining balance payment is accepted
# ---------------------------------------------------------------------------

def test_payment_exact_balance_accepted() -> None:
    """Sale total R$180.00, already paid R$160.00, remaining R$20.00.
    Registering R$20.00 must be accepted. Final balance: R$180.00, remaining: R$0.00.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Exato {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 100)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            # Template with price R$180.00
            template = _create_template(client, product["id"], 1, "180.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            # Register R$160.00
            _record_payment(client, sale["id"], "100.00", "PIX", str(uuid4()))
            _record_payment(client, sale["id"], "60.00", "PIX", str(uuid4()))

            # Register exact remaining R$20.00 — should be accepted
            res = client.post(
                f"/api/v1/sales/{sale['id']}/payments",
                json={"amount": "20.00", "method": "PIX", "idempotency_key": str(uuid4())},
            )
            assert res.status_code == 201, f"Exact payment should be accepted: {res.text}"

            # Verify total paid is R$180.00
            total_res = client.get(f"/api/v1/sales/{sale['id']}/payments/total")
            assert total_res.status_code == 200
            assert Decimal(total_res.json()["total_paid"]) == Decimal("180.00")
            assert Decimal(total_res.json()["sale_total"]) == Decimal("180.00")

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 12: AC-M5-043 — Concurrent excess payment: only one accepted
# ---------------------------------------------------------------------------

def test_payment_excess_concurrent() -> None:
    """Sale total R$175.00, already paid R$150.00, remaining R$25.00.
    Two concurrent payments of R$25.00 each with different idempotency keys.
    Only one should be accepted; the other must be rejected.
    Total paid must never exceed R$175.00.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto Conc {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 100)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            # Template with price R$175.00
            template = _create_template(client, product["id"], 1, "175.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            # Register R$150.00
            _record_payment(client, sale["id"], "100.00", "PIX", str(uuid4()))
            _record_payment(client, sale["id"], "50.00", "PIX", str(uuid4()))

            # Verify total paid is R$150.00
            total_res = client.get(f"/api/v1/sales/{sale['id']}/payments/total")
            assert total_res.status_code == 200
            assert Decimal(total_res.json()["total_paid"]) == Decimal("150.00")

            key1 = str(uuid4())
            key2 = str(uuid4())
            results: list[int] = []

            def do_payment_1() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    res = c.post(
                        f"/api/v1/sales/{sale['id']}/payments",
                        json={"amount": "25.00", "method": "PIX", "idempotency_key": key1},
                    )
                    return res.status_code

            def do_payment_2() -> int:
                with TestClient(__import__("app.main", fromlist=["app"]).app) as c:
                    res = c.post(
                        f"/api/v1/sales/{sale['id']}/payments",
                        json={"amount": "25.00", "method": "PIX", "idempotency_key": key2},
                    )
                    return res.status_code

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(do_payment_1), executor.submit(do_payment_2)]
                for f in as_completed(futures, timeout=30):
                    results.append(f.result())

            # Exactly one should succeed, one should fail
            assert len(results) == 2
            assert 201 in results, f"Expected one success (201), got: {results}"
            assert 409 in results, f"Expected one rejection (409), got: {results}"

            # Total paid must not exceed R$175.00
            total_res = client.get(f"/api/v1/sales/{sale['id']}/payments/total")
            assert total_res.status_code == 200
            final_total = Decimal(total_res.json()["total_paid"])
            assert final_total <= Decimal("175.00"), (
                f"Total paid R${final_total} exceeds sale total R$175.00"
            )

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 13: RES-007 — Reduction releases only unconsumed reserved quantity
# ---------------------------------------------------------------------------

def test_res007_reduction_releases_only_unconsumed() -> None:
    """RES-007: Reductions release only quantities still reserved, not consumed.

    Scenario (mixed state: partially consumed + partially unconsumed):
    1. Create sale with 3 units, confirm (reserved=3, consumed=0).
    2. Start preparation — consumes fully (reserved=3, consumed=3).
    3. Increase composition to 5 units — reserved=5, consumed=3, unconsumed=2.
    4. Reduce composition to 4 units — expected: reserved=4, consumed=3
       (released 1 from unconsumed portion).
    5. Verify reserved_quantity >= consumed_quantity (invariant).
    6. Verify no ENTRY movement was created (RES-008).
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto RES007 {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            _add_stock(client, product["id"], 100)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            # Template: 3 units of the product
            template = _create_template(client, product["id"], 3, "30.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            # Record payment >= 50%
            _record_payment(client, sale["id"], "30.00", "PIX", str(uuid4()))

            # Confirm sale — creates reservations (reserved=3, consumed=0)
            confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
            assert confirm_res.status_code == 200, f"Confirm failed: {confirm_res.text}"

            # Get basket ID
            sale_detail = client.get(f"/api/v1/sales/{sale['id']}").json()
            basket_id = sale_detail["baskets"][0]["id"]

            # Start preparation — consumes fully (reserved=3, consumed=3)
            prep_res = client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
            assert prep_res.status_code == 200, f"Prep start failed: {prep_res.text}"

            # Verify reservation state after preparation
            with SessionLocal() as db:
                reservation = db.query(SaleStockReservation).filter(
                    SaleStockReservation.sale_id == sale["id"],
                    SaleStockReservation.product_id == product["id"],
                ).one_or_none()
                assert reservation is not None
                assert reservation.reserved_quantity == 3
                assert reservation.consumed_quantity == 3

            # Step 3: Increase composition to 5 units
            # reserved becomes 5, consumed stays 3, unconsumed = 2
            # Sale is in EM_PREPARAÇÃO, so confirmed_warning is required
            increase_res = client.put(
                f"/api/v1/sales/{sale['id']}/baskets/{basket_id}/composition",
                json={
                    "items": [{"product_id": product["id"], "quantity": "5"}],
                    "operator_name": "Teste RES007",
                    "confirmed_warning": True,
                },
            )
            assert increase_res.status_code == 200, f"Increase failed: {increase_res.text}"

            with SessionLocal() as db:
                reservation = db.query(SaleStockReservation).filter(
                    SaleStockReservation.sale_id == sale["id"],
                    SaleStockReservation.product_id == product["id"],
                ).one_or_none()
                assert reservation is not None
                assert reservation.reserved_quantity == 5, f"Expected reserved=5, got {reservation.reserved_quantity}"
                assert reservation.consumed_quantity == 3, f"Expected consumed=3, got {reservation.consumed_quantity}"

            # Count ENTRY movements before reduction
            with SessionLocal() as db:
                entry_movements_before = db.query(InventoryMovement).filter(
                    InventoryMovement.sale_id == sale["id"],
                    InventoryMovement.type == "ENTRY",
                ).count()

            # Step 4: Reduce composition to 4 units
            # difference=1, unconsumed=2, release_amount=min(1,2)=1
            # Expected: reserved=4, consumed=3
            reduce_res = client.put(
                f"/api/v1/sales/{sale['id']}/baskets/{basket_id}/composition",
                json={
                    "items": [{"product_id": product["id"], "quantity": "4"}],
                    "operator_name": "Teste RES007",
                    "confirmed_warning": True,
                },
            )
            assert reduce_res.status_code == 200, f"Reduce failed: {reduce_res.text}"

            # Step 5: Verify reservation state
            with SessionLocal() as db:
                reservation = db.query(SaleStockReservation).filter(
                    SaleStockReservation.sale_id == sale["id"],
                    SaleStockReservation.product_id == product["id"],
                ).one_or_none()
                assert reservation is not None
                assert reservation.reserved_quantity == 4, (
                    f"Expected reserved=4 after reduction, got {reservation.reserved_quantity}"
                )
                assert reservation.consumed_quantity == 3, (
                    f"Expected consumed=3 (unchanged), got {reservation.consumed_quantity}"
                )
                # Invariant: reserved >= consumed
                assert reservation.reserved_quantity >= reservation.consumed_quantity, (
                    f"Invariant violated: reserved={reservation.reserved_quantity} < consumed={reservation.consumed_quantity}"
                )

            # Step 6: Verify no ENTRY movement was created (RES-008)
            with SessionLocal() as db:
                entry_movements_after = db.query(InventoryMovement).filter(
                    InventoryMovement.sale_id == sale["id"],
                    InventoryMovement.type == "ENTRY",
                ).count()
                # No ENTRY movement should be created by the reduction
                assert entry_movements_after == entry_movements_before, (
                    f"ENTRY movement created by reduction: {entry_movements_after - entry_movements_before} new ENTRY movements"
                )

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)


# ---------------------------------------------------------------------------
# Test 14: RES-009 — Reopen does not repeat physical write-offs
# ---------------------------------------------------------------------------

def test_res009_reopen_does_not_repeat_writeoffs() -> None:
    """RES-009: Reopening a PRONTA sale to EM_PREPARACAO must not repeat
    physical write-offs already performed during the previous preparation.

    Before/after comparison:
    - OUTPUT movement count must be unchanged.
    - Physical balance must be unchanged.
    - consumed_quantity must be unchanged.
    - reserved_quantity must be unchanged.
    - No ENTRY movement should be created.
    """
    sale_ids: list[int] = []
    product_ids: list[int] = []
    customer_ids: list[int] = []
    template_ids: list[int] = []

    try:
        with TestClient(__import__("app.main", fromlist=["app"]).app) as client:
            product = _create_product(client, f"Produto RES009 {uuid4().hex[:8]}")
            product_ids.append(product["id"])
            initial_stock = 100
            _add_stock(client, product["id"], initial_stock)

            customer = _create_customer(client)
            customer_ids.append(customer["id"])

            # Template: 3 units
            template = _create_template(client, product["id"], 3, "30.00")
            template_ids.append(template["id"])

            sale = _create_sale(
                client, customer["id"], template["id"],
                {"recipient_name": "Ana", "delivery_address": "Rua 1", "delivery_date": "2026-12-25", "delivery_time": "10:00"},
            )
            sale_ids.append(sale["id"])

            # Record payment >= 50%
            _record_payment(client, sale["id"], "30.00", "PIX", str(uuid4()))

            # Confirm sale
            confirm_res = client.post(f"/api/v1/sales/{sale['id']}/confirm")
            assert confirm_res.status_code == 200, f"Confirm failed: {confirm_res.text}"

            # Get basket ID
            sale_detail = client.get(f"/api/v1/sales/{sale['id']}").json()
            basket_id = sale_detail["baskets"][0]["id"]

            # Start preparation — creates OUTPUT movement, consumed=3
            prep_res = client.post(f"/api/v1/sales/{sale['id']}/start-preparation")
            assert prep_res.status_code == 200, f"Prep start failed: {prep_res.text}"

            # Mark basket as prepared — sale becomes PRONTA
            mark_res = client.post(f"/api/v1/sales/{sale['id']}/baskets/{basket_id}/prepare")
            assert mark_res.status_code == 200, f"Mark prepared failed: {mark_res.text}"

            sale_detail = client.get(f"/api/v1/sales/{sale['id']}").json()
            assert sale_detail["status"] == "PRONTA", f"Expected PRONTA, got {sale_detail['status']}"

            # --- Register state BEFORE reopen ---
            with SessionLocal() as db:
                output_count_before = db.query(InventoryMovement).filter(
                    InventoryMovement.sale_id == sale["id"],
                    InventoryMovement.type == "OUTPUT",
                ).count()

                entry_count_before = db.query(InventoryMovement).filter(
                    InventoryMovement.sale_id == sale["id"],
                    InventoryMovement.type == "ENTRY",
                ).count()

                reservation = db.query(SaleStockReservation).filter(
                    SaleStockReservation.sale_id == sale["id"],
                    SaleStockReservation.product_id == product["id"],
                ).one_or_none()
                assert reservation is not None
                consumed_before = reservation.consumed_quantity
                reserved_before = reservation.reserved_quantity

            balance_before = _get_balance(client, product["id"])

            # --- Reopen the sale ---
            reopen_res = client.post(
                f"/api/v1/sales/{sale['id']}/reopen",
                json={"reason": "Reabertura para teste RES-009", "operator_name": "Teste RES009"},
            )
            assert reopen_res.status_code == 200, f"Reopen failed: {reopen_res.text}"

            sale_detail = client.get(f"/api/v1/sales/{sale['id']}").json()
            assert sale_detail["status"] == "EM PREPARAÇÃO", (
                f"Expected EM PREPARAÇÃO after reopen, got {sale_detail['status']}"
            )

            # --- Verify state AFTER reopen ---
            with SessionLocal() as db:
                output_count_after = db.query(InventoryMovement).filter(
                    InventoryMovement.sale_id == sale["id"],
                    InventoryMovement.type == "OUTPUT",
                ).count()

                entry_count_after = db.query(InventoryMovement).filter(
                    InventoryMovement.sale_id == sale["id"],
                    InventoryMovement.type == "ENTRY",
                ).count()

                reservation = db.query(SaleStockReservation).filter(
                    SaleStockReservation.sale_id == sale["id"],
                    SaleStockReservation.product_id == product["id"],
                ).one_or_none()
                assert reservation is not None

                # OUTPUT count must be unchanged — no new write-off
                assert output_count_after == output_count_before, (
                    f"OUTPUT count changed: {output_count_before} -> {output_count_after}"
                )

                # ENTRY count must be 0 — no improper reintegration
                assert entry_count_after == entry_count_before, (
                    f"ENTRY count changed: {entry_count_before} -> {entry_count_after}"
                )

                # consumed_quantity must be unchanged
                assert reservation.consumed_quantity == consumed_before, (
                    f"consumed_quantity changed: {consumed_before} -> {reservation.consumed_quantity}"
                )

                # reserved_quantity must be unchanged
                assert reservation.reserved_quantity == reserved_before, (
                    f"reserved_quantity changed: {reserved_before} -> {reservation.reserved_quantity}"
                )

            # Physical balance must be unchanged
            balance_after = _get_balance(client, product["id"])
            assert balance_after == balance_before, (
                f"Physical balance changed: {balance_before} -> {balance_after}"
            )

    finally:
        _cleanup_test_data(product_ids, customer_ids, template_ids, sale_ids)
