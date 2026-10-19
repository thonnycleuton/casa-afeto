"""Test commercial conversion factor for reference price calculation.

The reference_price is stored as the price of the commercial unit (e.g., a box).
The commercial_conversion_factor tells the system how many base units are in
the commercial unit. The base unit price = reference_price / factor.
"""
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.baskets.service import _base_unit_reference_price
from app.products.models import Product


@pytest.fixture
def product_with_conversion():
    """Create a product with reference_price and commercial_conversion_factor."""
    name = f"conv-{uuid4().hex}"
    with SessionLocal() as db:
        product = Product(
            name=name,
            base_unit="UN",
            reference_price=Decimal("59.90"),
            commercial_conversion_factor=Decimal("12"),
            active=True,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        yield product
        db.delete(product)
        db.commit()


@pytest.fixture
def product_without_conversion():
    """Create a product with reference_price but no conversion factor."""
    name = f"no-conv-{uuid4().hex}"
    with SessionLocal() as db:
        product = Product(
            name=name,
            base_unit="UN",
            reference_price=Decimal("12.50"),
            commercial_conversion_factor=None,
            active=True,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        yield product
        db.delete(product)
        db.commit()


class TestBaseUnitReferencePrice:
    """Test the _base_unit_reference_price helper function."""

    def test_divides_by_conversion_factor(self, product_with_conversion):
        """reference_price / commercial_conversion_factor = base unit price."""
        base_price = _base_unit_reference_price(product_with_conversion)
        # 59.90 / 12 = 4.991666... → rounded to 4.99
        assert base_price == Decimal("4.99")

    def test_returns_reference_price_when_no_factor(self, product_without_conversion):
        """Without conversion factor, reference_price is already per base unit."""
        base_price = _base_unit_reference_price(product_without_conversion)
        assert base_price == Decimal("12.50")

    def test_returns_none_when_no_reference_price(self):
        """Product without reference_price returns None."""
        product = Product(
            name="no-price",
            base_unit="UN",
            reference_price=None,
            commercial_conversion_factor=Decimal("10"),
            active=True,
        )
        assert _base_unit_reference_price(product) is None


class TestCommercialConversionFactorAPI:
    """Test the API handles commercial_conversion_factor correctly."""

    def test_create_product_with_conversion_factor(self, client: TestClient):
        """Product can be created with commercial_conversion_factor."""
        payload = {
            "name": f"api-conv-{uuid4().hex}",
            "base_unit": "UN",
            "reference_price": "59.90",
            "commercial_conversion_factor": "12",
        }
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["reference_price"] == "59.90"
        assert data["commercial_conversion_factor"] == "12.00"

    def test_create_product_without_conversion_factor(self, client: TestClient):
        """Product can be created without commercial_conversion_factor."""
        payload = {
            "name": f"api-no-conv-{uuid4().hex}",
            "base_unit": "UN",
            "reference_price": "12.50",
        }
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["reference_price"] == "12.50"
        assert data["commercial_conversion_factor"] is None

    def test_update_product_conversion_factor(self, client: TestClient):
        """Product conversion factor can be updated."""
        payload = {
            "name": f"api-update-conv-{uuid4().hex}",
            "base_unit": "UN",
        }
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 201
        product_id = response.json()["id"]

        update = {"commercial_conversion_factor": "24"}
        response = client.patch(f"/api/v1/products/{product_id}", json=update)
        assert response.status_code == 200
        assert response.json()["commercial_conversion_factor"] == "24.00"

    def test_reject_negative_conversion_factor(self, client: TestClient):
        """Negative conversion factor is rejected."""
        payload = {
            "name": f"api-neg-conv-{uuid4().hex}",
            "base_unit": "UN",
            "commercial_conversion_factor": "-5",
        }
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 422

    def test_reject_zero_conversion_factor(self, client: TestClient):
        """Zero conversion factor is rejected."""
        payload = {
            "name": f"api-zero-conv-{uuid4().hex}",
            "base_unit": "UN",
            "commercial_conversion_factor": "0",
        }
        response = client.post("/api/v1/products", json=payload)
        assert response.status_code == 422


class TestTemplateSuggestedPriceWithConversion:
    """Test that template suggested_price uses base unit price when conversion factor is set."""

    def test_suggested_price_uses_base_unit_price(self, client: TestClient):
        """
        Template with product: reference_price=59.90, factor=12, quantity=2.
        Base unit price = 59.90/12 = 4.99.
        Reference cost = 2 * 4.99 = 9.98.
        Suggested price = 2 * 9.98 = 19.96.
        """
        # Create product with conversion factor
        prod_payload = {
            "name": f"tmpl-conv-{uuid4().hex}",
            "base_unit": "UN",
            "reference_price": "59.90",
            "commercial_conversion_factor": "12",
        }
        prod_resp = client.post("/api/v1/products", json=prod_payload)
        assert prod_resp.status_code == 201
        product_id = prod_resp.json()["id"]

        # Add inventory so stock is available
        client.post(f"/api/v1/products/{product_id}/inventory/entries", json={
            "quantity": "100"
        })

        # Create template with 2 units of the product
        tmpl_payload = {
            "name": f"Template com conversão {uuid4().hex[:8]}",
            "items": [{"product_id": product_id, "quantity": "2"}],
        }
        tmpl_resp = client.post("/api/v1/basket-templates", json=tmpl_payload)
        assert tmpl_resp.status_code == 201
        tmpl = tmpl_resp.json()

        # Base unit price = 59.90 / 12 = 4.99
        # Reference cost = 2 * 4.99 = 9.98
        # Suggested price = 2 * 9.98 = 19.96
        assert tmpl["suggested_price"] == "19.96"
        assert tmpl["estimated_cost"] == "9.98"

    def test_suggested_price_without_conversion_factor(self, client: TestClient):
        """
        Template with product: reference_price=12.50, no factor, quantity=2.
        Reference cost = 2 * 12.50 = 25.00.
        Suggested price = 2 * 25.00 = 50.00.
        """
        prod_payload = {
            "name": f"tmpl-no-conv-{uuid4().hex}",
            "base_unit": "UN",
            "reference_price": "12.50",
        }
        prod_resp = client.post("/api/v1/products", json=prod_payload)
        assert prod_resp.status_code == 201
        product_id = prod_resp.json()["id"]

        client.post(f"/api/v1/products/{product_id}/inventory/entries", json={
            "quantity": "100"
        })

        tmpl_payload = {
            "name": f"Template sem conversão {uuid4().hex[:8]}",
            "items": [{"product_id": product_id, "quantity": "2"}],
        }
        tmpl_resp = client.post("/api/v1/basket-templates", json=tmpl_payload)
        assert tmpl_resp.status_code == 201
        tmpl = tmpl_resp.json()

        assert tmpl["suggested_price"] == "50.00"
        assert tmpl["estimated_cost"] == "25.00"
