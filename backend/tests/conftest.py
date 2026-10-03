import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Fixture providing a FastAPI TestClient."""
    return TestClient(app)
