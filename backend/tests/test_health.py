from fastapi.testclient import TestClient

from app.core.config import settings


def test_health_endpoint(client: TestClient) -> None:
    """Verify that root /health endpoint responds with HTTP 200 and valid schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["environment"] == settings.ENVIRONMENT
    assert data["project_name"] == settings.PROJECT_NAME


def test_api_v1_health_endpoint(client: TestClient) -> None:
    """Verify that /api/v1/health endpoint responds with HTTP 200 and valid schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["environment"] == settings.ENVIRONMENT
    assert data["project_name"] == settings.PROJECT_NAME


def test_openapi_schema(client: TestClient) -> None:
    """Verify that OpenAPI documentation schema is exposed and valid."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert "/health" in schema["paths"]
    assert "/api/v1/health" in schema["paths"]
