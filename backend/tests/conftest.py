from collections.abc import Callable, Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.products.models import InventoryMovement, Product


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Fixture providing a FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def register_product_for_cleanup() -> Iterator[Callable[[int], None]]:
    product_ids: list[int] = []
    yield product_ids.append
    with SessionLocal() as db:
        db.query(InventoryMovement).filter(
            InventoryMovement.product_id.in_(product_ids)
        ).delete(synchronize_session=False)
        db.query(Product).filter(Product.id.in_(product_ids)).delete(
            synchronize_session=False
        )
        db.commit()


@pytest.fixture
def product_payload() -> dict[str, str]:
    return {"name": f"test-{uuid4().hex}", "base_unit": "UN"}
