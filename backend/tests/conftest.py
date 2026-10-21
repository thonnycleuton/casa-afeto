from collections.abc import Callable, Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.products.models import InventoryMovement, Product
from app.purchases.models import PurchaseItem, Purchase
from app.inventory.models import StockBatch


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Fixture providing a FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def register_product_for_cleanup() -> Iterator[Callable[[int], None]]:
    product_ids: list[int] = []
    yield product_ids.append
    with SessionLocal() as db:
        # Clean up purchase items first (RESTRICT FK on product_id)
        purchase_ids = db.query(PurchaseItem.purchase_id).filter(
            PurchaseItem.product_id.in_(product_ids)
        ).distinct().all()
        purchase_id_list = [p[0] for p in purchase_ids]
        if purchase_id_list:
            db.query(PurchaseItem).filter(
                PurchaseItem.purchase_id.in_(purchase_id_list)
            ).delete(synchronize_session=False)
            db.query(Purchase).filter(
                Purchase.id.in_(purchase_id_list)
            ).delete(synchronize_session=False)
        # Clean up stock batches first (RESTRICT FK from movements)
        db.query(StockBatch).filter(
            StockBatch.product_id.in_(product_ids)
        ).delete(synchronize_session=False)
        # Clean up inventory movements
        db.query(InventoryMovement).filter(
            InventoryMovement.product_id.in_(product_ids)
        ).delete(synchronize_session=False)
        # Clean up products
        db.query(Product).filter(Product.id.in_(product_ids)).delete(
            synchronize_session=False
        )
        db.commit()


@pytest.fixture
def product_payload() -> dict[str, str]:
    return {"name": f"test-{uuid4().hex}", "base_unit": "UN"}
