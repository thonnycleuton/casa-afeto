#!/usr/bin/env python3
"""
M5 API Validation Script
========================

Automates the M5 validation scenarios that require direct API calls
and cannot be easily tested via the UI.

Scenarios covered (11 scenarios, 54 assertions):
1. Payment idempotency (same key, same content)
2. Payment idempotency conflict (same key, different content)
3. Payment method validation (PIX, CARTAO accepted; DINHEIRO, OUTRO rejected)
4. Payment excess rejection
5. Payment exact balance acceptance
6. Composition edit on confirmed sale
7. Inspection and reintegration flow
8. Stock adjustment with active reservations
9. Reopen sale PRONTA without repeating stock deductions
10. Concurrent payment idempotency
11. Concurrent excess payment

Usage:
    python backend/tests/m5_api_validation.py

Requirements:
    - Backend running on http://localhost:8000
    - Database populated with M1-M5 migrations
"""

import sys
import json
import time
import uuid
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required. Install it with: pip install requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:8000/api/v1"
SESSION_ID = uuid.uuid4().hex[:8]  # Unique prefix for test data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class ValidationResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def assert_ok(self, condition: bool, message: str):
        if condition:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            self.errors.append(message)
            print(f"  ✗ {message}")

    def summary(self) -> str:
        total = self.passed + self.failed
        status = "PASS" if self.failed == 0 else "FAIL"
        return f"[{status}] {self.passed}/{total} checks passed"


def api_call(method: str, path: str, payload=None, expect_status=None):
    """Make an API call and return the response."""
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    resp = requests.request(method, url, json=payload, headers=headers, timeout=30)
    if expect_status and resp.status_code != expect_status:
        print(f"    WARNING: Expected {expect_status}, got {resp.status_code}: {resp.text[:200]}")
    return resp


def create_product(name: str) -> dict:
    resp = api_call("POST", "/products", {"name": f"{name} {SESSION_ID}", "base_unit": "UN"})
    return resp.json()


def add_stock(product_id: int, quantity: int) -> None:
    api_call("POST", f"/products/{product_id}/inventory/entries", {"quantity": str(quantity)})


def get_balance(product_id: int) -> Decimal:
    resp = api_call("GET", f"/products/{product_id}/inventory/balance")
    return Decimal(resp.json()["quantity"])


def create_customer() -> dict:
    resp = api_call("POST", "/customers", {
        "name": f"Cliente Validação {SESSION_ID}",
        "phone": f"119{uuid.uuid4().hex[:8]}"
    })
    return resp.json()


def create_template(product_id: int, quantity: int, price: str) -> dict:
    resp = api_call("POST", "/basket-templates", {
        "name": f"Cesta Validação {SESSION_ID}",
        "price": price,
        "items": [{"product_id": product_id, "quantity": str(quantity)}]
    })
    return resp.json()


def create_sale(customer_id: int, template_id: int, delivery_data=None) -> dict:
    baskets = [{
        "template_id": template_id,
        "recipient_name": delivery_data.get("recipient_name", "Teste") if delivery_data else None,
        "delivery_address": delivery_data.get("delivery_address", "Rua Teste") if delivery_data else None,
        "delivery_date": delivery_data.get("delivery_date", "2026-12-25") if delivery_data else None,
        "delivery_time": delivery_data.get("delivery_time", "10:00") if delivery_data else None,
    }]
    resp = api_call("POST", "/sales", {"customer_id": customer_id, "baskets": baskets})
    return resp.json()


def record_payment(sale_id: int, amount: str, method: str, key: str) -> requests.Response:
    return api_call("POST", f"/sales/{sale_id}/payments", {
        "amount": amount,
        "method": method,
        "idempotency_key": key
    })


def confirm_sale(sale_id: int) -> requests.Response:
    return api_call("POST", f"/sales/{sale_id}/confirm")


def start_preparation(sale_id: int) -> requests.Response:
    return api_call("POST", f"/sales/{sale_id}/start-preparation")


def mark_basket_prepared(sale_id: int, basket_id: int) -> requests.Response:
    return api_call("POST", f"/sales/{sale_id}/baskets/{basket_id}/prepare")


def cancel_sale(sale_id: int) -> requests.Response:
    return api_call("POST", f"/sales/{sale_id}/cancel")


def get_sale(sale_id: int) -> dict:
    resp = api_call("GET", f"/sales/{sale_id}")
    return resp.json()


def get_payments(sale_id: int) -> list:
    resp = api_call("GET", f"/sales/{sale_id}/payments")
    return resp.json()


def get_payment_total(sale_id: int) -> dict:
    resp = api_call("GET", f"/sales/{sale_id}/payments/total")
    return resp.json()


def get_inspections(sale_id: int) -> list:
    resp = api_call("GET", f"/sales/{sale_id}/inspections")
    return resp.json()


def record_inspection(sale_id: int, inspection_id: int, inspected_qty: str, reusable_qty: str) -> requests.Response:
    return api_call("POST", f"/sales/{sale_id}/inspections/{inspection_id}/record", {
        "inspected_quantity": inspected_qty,
        "reusable_quantity": reusable_qty,
        "operator_name": "Validador API"
    })


def reintegrate_inspection(sale_id: int, inspection_id: int, quantity: str) -> requests.Response:
    return api_call("POST", f"/sales/{sale_id}/inspections/{inspection_id}/reintegrate", {
        "quantity": quantity,
        "operator_name": "Validador API"
    })


def update_composition(sale_id: int, basket_id: int, items: list, confirmed_warning: bool = False) -> requests.Response:
    return api_call("PUT", f"/sales/{sale_id}/baskets/{basket_id}/composition", {
        "items": items,
        "operator_name": "Validador API",
        "confirmed_warning": confirmed_warning
    })


def adjust_inventory(product_id: int, quantity: str) -> requests.Response:
    return api_call("POST", f"/products/{product_id}/inventory/adjustments", {"quantity": quantity})


def check_availability(product_id: int, quantity: str) -> dict:
    resp = api_call("POST", f"/products/{product_id}/inventory/availability", {"quantity": quantity})
    return resp.json()


def setup_test_data():
    """Create shared test data: product, stock, customer, template."""
    product = create_product("Produto Validação M5")
    add_stock(product["id"], 100)

    customer = create_customer()

    # Template: 1 unit at R$100.00
    template = create_template(product["id"], 1, "100.00")

    return product, customer, template


def print_scenario(num: int, title: str):
    print(f"\n{'='*60}")
    print(f"Cenário {num}: {title}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Scenario 1: Payment Idempotency — Same Key, Same Content
# ---------------------------------------------------------------------------

def scenario_idempotency_same_content(result: ValidationResult):
    print_scenario(1, "Idempotência — mesma chave, mesmo conteúdo")

    product, customer, template = setup_test_data()
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    key = str(uuid.uuid4())

    # First payment
    resp1 = record_payment(sale["id"], "50.00", "PIX", key)
    result.assert_ok(resp1.status_code == 201, "Primeiro pagamento aceito (201)")

    # Second payment with same key — should return existing payment
    resp2 = record_payment(sale["id"], "50.00", "PIX", key)
    result.assert_ok(resp2.status_code in (200, 201), "Segundo pagamento com mesma chave retorna pagamento existente")

    # Verify only one payment in DB
    payments = get_payments(sale["id"])
    result.assert_ok(len(payments) == 1, f"Apenas 1 pagamento no banco (encontrado {len(payments)})")


# ---------------------------------------------------------------------------
# Scenario 2: Payment Idempotency — Same Key, Different Content
# ---------------------------------------------------------------------------

def scenario_idempotency_conflict(result: ValidationResult):
    print_scenario(2, "Idempotência — mesma chave, conteúdo diferente")

    product, customer, template = setup_test_data()
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    key = str(uuid.uuid4())

    # First payment: R$50.00
    resp1 = record_payment(sale["id"], "50.00", "PIX", key)
    result.assert_ok(resp1.status_code == 201, "Primeiro pagamento aceito (201)")

    # Second payment with same key but different amount — should conflict
    resp2 = record_payment(sale["id"], "75.00", "PIX", key)
    result.assert_ok(resp2.status_code == 409, "Conflito de idempotência rejeitado (409)")

    # Verify only one payment
    payments = get_payments(sale["id"])
    result.assert_ok(len(payments) == 1, f"Apenas 1 pagamento no banco (encontrado {len(payments)})")


# ---------------------------------------------------------------------------
# Scenario 3: Payment Method Validation
# ---------------------------------------------------------------------------

def scenario_payment_methods(result: ValidationResult):
    print_scenario(3, "Validação de método de pagamento")

    product, customer, template = setup_test_data()
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    # PIX — accepted
    resp = record_payment(sale["id"], "10.00", "PIX", str(uuid.uuid4()))
    result.assert_ok(resp.status_code == 201, "PIX aceito (201)")

    # CARTAO — accepted
    resp = record_payment(sale["id"], "10.00", "CARTAO", str(uuid.uuid4()))
    result.assert_ok(resp.status_code == 201, "CARTAO aceito (201)")

    # DINHEIRO — rejected
    resp = record_payment(sale["id"], "10.00", "DINHEIRO", str(uuid.uuid4()))
    result.assert_ok(resp.status_code == 422, "DINHEIRO rejeitado (422)")

    # OUTRO — rejected
    resp = record_payment(sale["id"], "10.00", "OUTRO", str(uuid.uuid4()))
    result.assert_ok(resp.status_code == 422, "OUTRO rejeitado (422)")

    # BOLETO — rejected
    resp = record_payment(sale["id"], "10.00", "BOLETO", str(uuid.uuid4()))
    result.assert_ok(resp.status_code == 422, "BOLETO rejeitado (422)")


# ---------------------------------------------------------------------------
# Scenario 4: Payment Excess Rejection
# ---------------------------------------------------------------------------

def scenario_payment_excess(result: ValidationResult):
    print_scenario(4, "Pagamento excedente rejeitado")

    product, customer, template = setup_test_data()
    # Template price: R$180.00
    template = create_template(product["id"], 1, "180.00")
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    # Register R$160.00
    record_payment(sale["id"], "100.00", "PIX", str(uuid.uuid4()))
    record_payment(sale["id"], "60.00", "PIX", str(uuid.uuid4()))

    total = get_payment_total(sale["id"])
    result.assert_ok(Decimal(total["total_paid"]) == Decimal("160.00"), f"Total pago: R${total['total_paid']}")

    # Try R$30.00 — should be rejected (160 + 30 = 190 > 180)
    resp = record_payment(sale["id"], "30.00", "PIX", str(uuid.uuid4()))
    result.assert_ok(resp.status_code == 409, "Pagamento excedente rejeitado (409)")

    # Verify total unchanged
    total = get_payment_total(sale["id"])
    result.assert_ok(Decimal(total["total_paid"]) == Decimal("160.00"), f"Total pago inalterado: R${total['total_paid']}")


# ---------------------------------------------------------------------------
# Scenario 5: Payment Exact Balance Acceptance
# ---------------------------------------------------------------------------

def scenario_payment_exact(result: ValidationResult):
    print_scenario(5, "Pagamento exato aceito")

    product, customer, template = setup_test_data()
    template = create_template(product["id"], 1, "180.00")
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    # Register R$160.00
    record_payment(sale["id"], "100.00", "PIX", str(uuid.uuid4()))
    record_payment(sale["id"], "60.00", "PIX", str(uuid.uuid4()))

    # Register exact remaining R$20.00
    resp = record_payment(sale["id"], "20.00", "PIX", str(uuid.uuid4()))
    result.assert_ok(resp.status_code == 201, "Pagamento exato aceito (201)")

    total = get_payment_total(sale["id"])
    result.assert_ok(Decimal(total["total_paid"]) == Decimal("180.00"), f"Total pago: R${total['total_paid']}")
    result.assert_ok(Decimal(total["sale_total"]) == Decimal("180.00"), f"Total venda: R${total['sale_total']}")


# ---------------------------------------------------------------------------
# Scenario 6: Composition Edit on Confirmed Sale
# ---------------------------------------------------------------------------

def scenario_composition_edit(result: ValidationResult):
    print_scenario(6, "Edição de composição em venda confirmada")

    product, customer, template = setup_test_data()
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    # Confirm the sale
    record_payment(sale["id"], "100.00", "PIX", str(uuid.uuid4()))
    confirm_resp = confirm_sale(sale["id"])
    result.assert_ok(confirm_resp.status_code == 200, "Venda confirmada (200)")

    sale_data = get_sale(sale["id"])
    result.assert_ok(sale_data["status"] == "CONFIRMADA", f"Status da venda: {sale_data['status']}")

    basket_id = sale_data["baskets"][0]["id"]

    # Edit composition: change quantity from 1 to 3
    resp = update_composition(sale["id"], basket_id, [
        {"product_id": product["id"], "quantity": "3"}
    ], confirmed_warning=True)
    result.assert_ok(resp.status_code == 200, "Composição atualizada (200)")

    # Verify new composition
    sale_data = get_sale(sale["id"])
    items = sale_data["baskets"][0]["items"]
    result.assert_ok(len(items) == 1, f"1 item na cesta (encontrado {len(items)})")
    if items:
        result.assert_ok(Decimal(items[0]["quantity"]) == Decimal("3"), f"Quantidade: {items[0]['quantity']}")


# ---------------------------------------------------------------------------
# Scenario 7: Inspection and Reintegration Flow
# ---------------------------------------------------------------------------

def scenario_inspection_reintegration(result: ValidationResult):
    print_scenario(7, "Inspeção e reintegração após cancelamento")

    product, customer, template = setup_test_data()
    # Template: 3 units
    template = create_template(product["id"], 3, "100.00")
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    # Record balance before confirmation (reservation does NOT change physical stock)
    balance_before_confirm = get_balance(product["id"])

    # Confirm
    record_payment(sale["id"], "100.00", "PIX", str(uuid.uuid4()))
    confirm_resp = confirm_sale(sale["id"])
    result.assert_ok(confirm_resp.status_code == 200, "Venda confirmada")

    # Balance should be unchanged after confirmation (reservation ≠ physical deduction)
    balance_after_confirm = get_balance(product["id"])
    result.assert_ok(balance_after_confirm == balance_before_confirm,
        f"Estoque inalterado após reserva: {balance_after_confirm} == {balance_before_confirm}")

    # Start preparation — deducts 3 units
    prep_resp = start_preparation(sale["id"])
    result.assert_ok(prep_resp.status_code == 200, "Preparação iniciada")

    balance_after_prep = get_balance(product["id"])
    result.assert_ok(balance_after_prep == balance_before_confirm - 3,
        f"Estoque reduzido em 3 após preparação: {balance_after_prep} (antes {balance_before_confirm})")

    # Cancel — should create inspection records
    cancel_resp = cancel_sale(sale["id"])
    result.assert_ok(cancel_resp.status_code == 200, "Venda cancelada")

    sale_data = get_sale(sale["id"])
    result.assert_ok(sale_data["status"] == "CANCELADA", f"Status: {sale_data['status']}")

    # Get inspections
    inspections = get_inspections(sale["id"])
    result.assert_ok(len(inspections) >= 1, f"Registro de inspeção criado ({len(inspections)} registros)")

    if inspections:
        inspection = inspections[0]
        result.assert_ok(inspection["status"] == "PENDING", f"Status inspeção: {inspection['status']}")

        # Record inspection: 2 reusable out of 3 consumed
        inspect_resp = record_inspection(sale["id"], inspection["id"], "3", "2")
        result.assert_ok(inspect_resp.status_code == 200, "Inspeção registrada")
        result.assert_ok(inspect_resp.json()["status"] == "INSPECTED", f"Status após inspeção: {inspect_resp.json()['status']}")

        # Reintegrate 2 units
        reintegrate_resp = reintegrate_inspection(sale["id"], inspection["id"], "2")
        result.assert_ok(reintegrate_resp.status_code == 200, "Reintegração realizada")
        result.assert_ok(reintegrate_resp.json()["status"] == "REINTEGRATED", f"Status após reintegração: {reintegrate_resp.json()['status']}")

        balance_after_reintegrate = get_balance(product["id"])
        result.assert_ok(balance_after_reintegrate == balance_after_prep + 2,
            f"Estoque aumentado em 2 após reintegração: {balance_after_reintegrate} (antes {balance_after_prep})")

        # Double reintegration should be blocked
        double_resp = reintegrate_inspection(sale["id"], inspection["id"], "1")
        result.assert_ok(double_resp.status_code == 409, "Reintegração duplicada bloqueada (409)")


# ---------------------------------------------------------------------------
# Scenario 8: Stock Adjustment with Active Reservations
# ---------------------------------------------------------------------------

def scenario_adjustment_with_reservations(result: ValidationResult):
    print_scenario(8, "Ajuste de estoque com reservas ativas")

    product, customer, template = setup_test_data()

    balance_before = get_balance(product["id"])

    # Template: 8 units
    template = create_template(product["id"], 8, "100.00")
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    # Confirm — reserves 8 units
    record_payment(sale["id"], "100.00", "PIX", str(uuid.uuid4()))
    confirm_resp = confirm_sale(sale["id"])
    result.assert_ok(confirm_resp.status_code == 200, "Venda confirmada (reserva de 8 unidades)")

    # Try adjustment of -5: if balance is 101 (100 from setup), resulting = 96, active_res = 8 -> allowed
    # We need to test the reservation coverage rule, so we use a large negative adjustment
    # that would bring balance below active reservations.
    # With balance ~101 and active_res = 8, we need adjustment that results in < 8.
    # -94 would result in 7 < 8 -> rejected
    # -2 would result in 99 >= 8 -> allowed
    # But the exact balance depends on previous scenarios, so we compute dynamically.
    # We test: a very large negative adjustment should be rejected if it violates coverage.
    large_negative = -(balance_before + 1000)  # Guaranteed to violate coverage
    resp = adjust_inventory(product["id"], str(large_negative))
    result.assert_ok(resp.status_code == 409,
        f"Ajuste negativo grande ({large_negative}) rejeitado (viola cobertura de reservas)")

    # Small adjustment of -2 should be allowed (balance >> 8)
    resp = adjust_inventory(product["id"], "-2")
    result.assert_ok(resp.status_code == 201, "Ajuste -2 permitido (dentro da cobertura)")

    balance_after = get_balance(product["id"])
    result.assert_ok(balance_after == balance_before - 2,
        f"Estoque reduzido em 2 após ajuste: {balance_after} (antes {balance_before})")


# ---------------------------------------------------------------------------
# Scenario 9: Full Flow — Confirm → Prep → Mark Ready → Reopen
# ---------------------------------------------------------------------------

def scenario_full_flow_reopen(result: ValidationResult):
    print_scenario(9, "Reabertura de venda PRONTA sem repetição de baixas")

    product, customer, template = setup_test_data()
    add_stock(product["id"], 90)  # Extra stock

    # Template: 3 units
    template = create_template(product["id"], 3, "30.00")
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    # Confirm
    record_payment(sale["id"], "30.00", "PIX", str(uuid.uuid4()))
    confirm_resp = confirm_sale(sale["id"])
    result.assert_ok(confirm_resp.status_code == 200, "Venda confirmada")

    sale_data = get_sale(sale["id"])
    basket_id = sale_data["baskets"][0]["id"]

    # Start preparation
    prep_resp = start_preparation(sale["id"])
    result.assert_ok(prep_resp.status_code == 200, "Preparação iniciada")

    # Mark basket as prepared — sale becomes PRONTA
    mark_resp = mark_basket_prepared(sale["id"], basket_id)
    result.assert_ok(mark_resp.status_code == 200, "Cesta marcada como preparada")

    sale_data = get_sale(sale["id"])
    result.assert_ok(sale_data["status"] == "PRONTA", f"Status: {sale_data['status']}")

    balance_before = get_balance(product["id"])

    # Reopen the sale
    reopen_resp = api_call("POST", f"/sales/{sale['id']}/reopen", {
        "reason": "Reabertura para validação",
        "operator_name": "Validador API"
    })
    result.assert_ok(reopen_resp.status_code == 200, "Venda reaberta (200)")

    sale_data = get_sale(sale["id"])
    result.assert_ok(sale_data["status"] == "EM PREPARAÇÃO", f"Status após reabertura: {sale_data['status']}")

    balance_after = get_balance(product["id"])
    result.assert_ok(balance_after == balance_before, f"Estoque inalterado após reabertura: {balance_after}")


# ---------------------------------------------------------------------------
# Scenario 10: Concurrent Payment Idempotency
# ---------------------------------------------------------------------------

def scenario_concurrent_idempotency(result: ValidationResult):
    print_scenario(10, "Idempotência de pagamento concorrente")

    product, customer, template = setup_test_data()
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    key = str(uuid.uuid4())
    results = []

    def do_payment() -> int:
        resp = record_payment(sale["id"], "50.00", "PIX", key)
        return resp.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(do_payment), executor.submit(do_payment)]
        for f in as_completed(futures, timeout=30):
            results.append(f.result())

    result.assert_ok(len(results) == 2, f"Dois resultados recebidos: {results}")
    result.assert_ok(all(s in (200, 201) for s in results), f"Ambos os pagamentos retornaram sucesso: {results}")

    payments = get_payments(sale["id"])
    result.assert_ok(len(payments) == 1, f"Apenas 1 pagamento no banco (concorrente): {len(payments)}")


# ---------------------------------------------------------------------------
# Scenario 11: Concurrent Excess Payment
# ---------------------------------------------------------------------------

def scenario_concurrent_excess_payment(result: ValidationResult):
    print_scenario(11, "Pagamento excedente concorrente")

    product, customer, template = setup_test_data()
    # Template: R$175.00
    template = create_template(product["id"], 1, "175.00")
    sale = create_sale(customer["id"], template["id"], {
        "recipient_name": "Ana", "delivery_address": "Rua 1",
        "delivery_date": "2026-12-25", "delivery_time": "10:00"
    })

    # Register R$150.00
    record_payment(sale["id"], "100.00", "PIX", str(uuid.uuid4()))
    record_payment(sale["id"], "50.00", "PIX", str(uuid.uuid4()))

    total = get_payment_total(sale["id"])
    result.assert_ok(Decimal(total["total_paid"]) == Decimal("150.00"), f"Total pago: R${total['total_paid']}")

    key1 = str(uuid.uuid4())
    key2 = str(uuid.uuid4())
    results = []

    def do_payment_1() -> int:
        resp = record_payment(sale["id"], "25.00", "PIX", key1)
        return resp.status_code

    def do_payment_2() -> int:
        resp = record_payment(sale["id"], "25.00", "PIX", key2)
        return resp.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(do_payment_1), executor.submit(do_payment_2)]
        for f in as_completed(futures, timeout=30):
            results.append(f.result())

    result.assert_ok(201 in results, f"Um pagamento aceito: {results}")
    result.assert_ok(409 in results, f"Um pagamento rejeitado: {results}")

    total = get_payment_total(sale["id"])
    final_total = Decimal(total["total_paid"])
    result.assert_ok(final_total <= Decimal("175.00"), f"Total pago não excede o total da venda: R${final_total}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("M5 API VALIDATION SCRIPT")
    print(f"Sessão: {SESSION_ID}")
    print(f"API: {BASE_URL}")
    print("=" * 60)

    # Check API connectivity
    try:
        health_resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_resp.status_code != 200:
            print(f"ERROR: API health check failed with status {health_resp.status_code}")
            sys.exit(1)
        print("✓ API está acessível")
    except requests.ConnectionError:
        print(f"ERROR: Não foi possível conectar à API em {BASE_URL}")
        print("Certifique-se de que o backend está rodando (docker-compose up)")
        sys.exit(1)

    result = ValidationResult()

    scenarios = [
        scenario_idempotency_same_content,
        scenario_idempotency_conflict,
        scenario_payment_methods,
        scenario_payment_excess,
        scenario_payment_exact,
        scenario_composition_edit,
        scenario_inspection_reintegration,
        scenario_adjustment_with_reservations,
        scenario_full_flow_reopen,
        scenario_concurrent_idempotency,
        scenario_concurrent_excess_payment,
    ]

    for scenario in scenarios:
        try:
            scenario(result)
        except Exception as e:
            result.failed += 1
            result.errors.append(f"Exception in {scenario.__name__}: {e}")
            print(f"  ✗ EXCEPTION: {e}")

    # Final summary
    print(f"\n{'='*60}")
    print("RESUMO FINAL")
    print(f"{'='*60}")
    print(result.summary())

    if result.errors:
        print(f"\nFalhas ({len(result.errors)}):")
        for err in result.errors:
            print(f"  - {err}")

    sys.exit(0 if result.failed == 0 else 1)


if __name__ == "__main__":
    main()
