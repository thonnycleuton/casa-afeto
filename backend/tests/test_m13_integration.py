"""M13 — Testes de integração: confirmação OCR → compra → estoque.

Cobre as duas lacunas identificadas na auditoria:

1. Fluxo completo OCR → compra → estoque com conversão não trivial.
   Cria sessão OCR real, executa confirm_import() sem mock de _create_purchase,
   e verifica Purchase, PurchaseItem, InventoryMovement e saldo de estoque.

2. Constraint UNIQUE da access_key no banco real.
   Cria duas compras com a mesma chave de acesso e verifica que a segunda
   é rejeitada pela constraint uq_purchases_access_key.
"""
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.ocr.schemas import (
    ConfirmImportRequest,
    ConfirmedItem,
    OCRItem,
    OCRSession,
)
from app.ocr.state import store
from app.products.models import InventoryMovement, Product
from app.purchases.models import Purchase, PurchaseItem


# ─── Helpers ──────────────────────────────────────────────────────────────


def _make_ocr_item(
    item_id: str = "item-1",
    quantity: Decimal = Decimal("2"),
    commercial_unit: str = "caixa",
    commercial_unit_price: Decimal = Decimal("48.00"),
    product_id: int | None = None,
    conversion_factor: Decimal = Decimal("24"),
) -> OCRItem:
    return OCRItem(
        item_id=item_id,
        description=f"Produto {item_id}",
        quantity=quantity,
        commercial_unit=commercial_unit,
        commercial_unit_price=commercial_unit_price,
        product_id=product_id,
        conversion_factor=conversion_factor,
    )


def _make_session(
    session_id: str,
    items: list[OCRItem],
    access_key: str = "1" * 44,
) -> OCRSession:
    return OCRSession(
        session_id=session_id,
        status="completed",
        items=items,
        access_key=access_key,
    )


def _make_request(
    confirmed_items: list[ConfirmedItem],
    excluded_item_ids: list[str] | None = None,
) -> ConfirmImportRequest:
    return ConfirmImportRequest(
        confirmed_items=confirmed_items,
        excluded_item_ids=excluded_item_ids or [],
    )


def _get_admin_headers(client: TestClient) -> dict[str, str]:
    """Create admin, login, and return auth headers."""
    email = f"admin-{uuid4().hex[:8]}@casaafeto.com"
    resp = client.post("/api/v1/auth/setup/create-admin", json={
        "email": email,
        "password": "Admin1234",
        "full_name": "Test Admin",
    })
    assert resp.status_code == 201, f"Setup failed: {resp.text}"
    tokens_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Admin1234",
    })
    assert tokens_resp.status_code == 200, f"Login failed: {tokens_resp.text}"
    tokens = tokens_resp.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _create_product(client: TestClient) -> dict:
    """Create a product via API and return the product dict."""
    name = f"ocr-integration-{uuid4().hex[:8]}"
    resp = client.post("/api/v1/products", json={"name": name, "base_unit": "UN"})
    assert resp.status_code == 201, f"Product creation failed: {resp.text}"
    return resp.json()


# ─── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clean_ocr_sessions():
    """Clean OCR sessions before and after each test."""
    store._sessions.clear()
    yield
    store._sessions.clear()


@pytest.fixture(autouse=True)
def clean_auth_data():
    """Clean all auth-related data before and after each test."""
    from app.auth.models import RefreshToken, PasswordResetToken, User
    with SessionLocal() as db:
        db.query(RefreshToken).delete(synchronize_session=False)
        db.query(PasswordResetToken).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.commit()
    yield
    with SessionLocal() as db:
        db.query(RefreshToken).delete(synchronize_session=False)
        db.query(PasswordResetToken).delete(synchronize_session=False)
        db.query(User).delete(synchronize_session=False)
        db.commit()


# ─── Test 1: OCR → Purchase → Stock end-to-end ───────────────────────────


class TestOCRToStockIntegration:
    """End-to-end: confirm_import() creates real Purchase, PurchaseItem,
    and InventoryMovement with non-trivial unit conversion.

    Scenario: 2 caixas × 24 unidades, preço R$48,00 por caixa.
    Expected: 48 UN em estoque, custo unitário R$2,00.
    """

    def test_confirm_import_creates_purchase_and_stock(
        self, client: TestClient
    ) -> None:
        """confirm_import() with real _create_purchase creates Purchase,
        PurchaseItem, InventoryMovement, and updates stock balance.
        """
        # 1. Create product via API
        product = _create_product(client)
        product_id = product["id"]

        # 2. Create OCR session in store
        session_id = f"int-{uuid4().hex[:8]}"
        session = _make_session(
            session_id=session_id,
            items=[
                _make_ocr_item(
                    item_id="item-1",
                    quantity=Decimal("2"),
                    commercial_unit="caixa",
                    commercial_unit_price=Decimal("48.00"),
                    product_id=product_id,
                    conversion_factor=Decimal("24"),
                )
            ],
        )
        store.add(session)

        # 3. Build confirmation request
        request = _make_request(
            confirmed_items=[
                ConfirmedItem(
                    item_id="item-1",
                    product_id=product_id,
                    commercial_quantity=Decimal("2"),
                    commercial_unit="caixa",
                    commercial_unit_price=Decimal("48.00"),
                    conversion_factor=Decimal("24"),
                )
            ]
        )
        request_json = request.model_dump(mode="json")

        # 4. Confirm via API endpoint (uses real confirm_import + real DB)
        headers = _get_admin_headers(client)
        resp = client.post(
            f"/api/v1/ocr/{session_id}/confirm",
            json=request_json,
            headers=headers,
        )
        assert resp.status_code == 200, f"Confirmation failed: {resp.text}"

        # 5. Verify response
        data = resp.json()
        assert data["purchase_id"] is not None
        purchase_id = data["purchase_id"]
        assert data["access_key"] == "1" * 44
        assert len(data["confirmed_items"]) == 1
        assert len(data["excluded_items"]) == 0

        # 6. Verify Purchase in database
        with SessionLocal() as db:
            purchase = db.get(Purchase, purchase_id)
            assert purchase is not None
            assert purchase.access_key == "1" * 44

            # 7. Verify PurchaseItem
            purchase_items = db.query(PurchaseItem).filter(
                PurchaseItem.purchase_id == purchase_id
            ).all()
            assert len(purchase_items) == 1
            item = purchase_items[0]
            assert item.product_id == product_id
            assert item.commercial_unit == "caixa"
            assert item.conversion_factor == Decimal("24")
            assert item.commercial_quantity == Decimal("2")
            assert item.commercial_unit_price == Decimal("48.00")

            # 8. Verify InventoryMovement
            movements = db.query(InventoryMovement).filter(
                InventoryMovement.product_id == product_id,
                InventoryMovement.purchase_id == purchase_id,
            ).all()
            assert len(movements) == 1
            movement = movements[0]
            # base_quantity = 2 × 24 = 48
            assert movement.quantity == Decimal("48")
            # unit_cost = 48.00 / 24 = 2.00
            assert movement.unit_cost == Decimal("2.00")

        # 9. Verify stock balance via API
        balance_resp = client.get(f"/api/v1/products/{product_id}/inventory/balance")
        assert balance_resp.status_code == 200
        balance = Decimal(balance_resp.json()["quantity"])
        assert balance == Decimal("48")

        # 10. Verify session removed from store
        assert session_id not in store

        # 11. Cleanup
        with SessionLocal() as db:
            from app.inventory.models import StockBatch

            purchase_ids = [
                m.purchase_id for m in db.query(InventoryMovement).filter(
                    InventoryMovement.product_id == product_id
                ).all()
            ]
            db.query(InventoryMovement).filter(
                InventoryMovement.product_id == product_id
            ).delete(synchronize_session=False)
            db.query(PurchaseItem).filter(
                PurchaseItem.product_id == product_id
            ).delete(synchronize_session=False)
            if purchase_ids:
                db.query(Purchase).filter(
                    Purchase.id.in_(purchase_ids)
                ).delete(synchronize_session=False)
            db.query(StockBatch).filter(
                StockBatch.product_id == product_id
            ).delete(synchronize_session=False)
            db.query(Product).filter(Product.id == product_id).delete(
                synchronize_session=False
            )
            db.commit()


# ─── Test 2: access_key UNIQUE constraint ────────────────────────────────


class TestAccessKeyUniqueConstraint:
    """Verify that the uq_purchases_access_key UNIQUE constraint
    is enforced by the real database.
    """

    def test_duplicate_access_key_rejected_by_database(
        self, client: TestClient
    ) -> None:
        """Two purchases with the same access_key: the second is rejected
        by the uq_purchases_access_key constraint.
        """
        # 1. Create product via API
        product = _create_product(client)
        product_id = product["id"]

        access_key = "2" * 44

        # 2. Create first purchase with access_key via API
        resp1 = client.post("/api/v1/purchases", json={
            "access_key": access_key,
            "items": [
                {
                    "product_id": product_id,
                    "commercial_unit": "un",
                    "conversion_factor": "1",
                    "commercial_quantity": "10",
                    "commercial_unit_price": "5.00",
                }
            ],
        })
        assert resp1.status_code == 201, f"First purchase failed: {resp1.text}"

        # 3. Create second purchase with the same access_key
        resp2 = client.post("/api/v1/purchases", json={
            "access_key": access_key,
            "items": [
                {
                    "product_id": product_id,
                    "commercial_unit": "un",
                    "conversion_factor": "1",
                    "commercial_quantity": "5",
                    "commercial_unit_price": "3.00",
                }
            ],
        })

        # 4. Verify the second purchase is rejected
        # The purchases endpoint doesn't have special IntegrityError handling,
        # so it returns 500 for database errors. We verify the constraint
        # was triggered by checking the database state.
        assert resp2.status_code != 201, (
            "Second purchase should have been rejected by UNIQUE constraint"
        )

        # 5. Verify only one purchase exists with this access_key
        with SessionLocal() as db:
            purchases = db.query(Purchase).filter(
                Purchase.access_key == access_key
            ).all()
            assert len(purchases) == 1, (
                f"Expected 1 purchase with access_key, found {len(purchases)}"
            )

        # 6. Cleanup
        with SessionLocal() as db:
            purchase_ids = [
                m.purchase_id for m in db.query(InventoryMovement).filter(
                    InventoryMovement.product_id == product_id
                ).all()
            ]
            db.query(InventoryMovement).filter(
                InventoryMovement.product_id == product_id
            ).delete(synchronize_session=False)
            db.query(PurchaseItem).filter(
                PurchaseItem.product_id == product_id
            ).delete(synchronize_session=False)
            if purchase_ids:
                db.query(Purchase).filter(
                    Purchase.id.in_(purchase_ids)
                ).delete(synchronize_session=False)
            from app.inventory.models import StockBatch
            db.query(StockBatch).filter(
                StockBatch.product_id == product_id
            ).delete(synchronize_session=False)
            db.query(Product).filter(Product.id == product_id).delete(
                synchronize_session=False
            )
            db.commit()
