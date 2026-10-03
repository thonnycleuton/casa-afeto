from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.core.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str
    environment: str
    project_name: str

    model_config = ConfigDict(extra="forbid")


def get_health_status() -> HealthResponse:
    """Return application health information."""
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        project_name=settings.PROJECT_NAME,
    )


@router.get("/health", response_model=HealthResponse, summary="Health Check")
def health_check() -> HealthResponse:
    """Return basic application status indicating the service is running."""
    return get_health_status()
