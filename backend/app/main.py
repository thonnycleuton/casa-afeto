from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.products import router as products_router
from app.core.config import settings
from app.core.errors import register_error_handlers


def create_application() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="Backend API for Casa Afeto Sales and Operations Management System",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Register routers:
    # 1. Directly under root for GET /health
    app.include_router(health_router)
    # 2. Under /api/v1 for REST API consistency GET /api/v1/health
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(products_router, prefix="/api/v1")
    register_error_handlers(app)

    return app


app = create_application()
