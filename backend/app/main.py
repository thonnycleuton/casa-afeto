from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.batches import router as batches_router
from app.api.v1.baskets import router as baskets_router
from app.api.v1.customers import router as customers_router
from app.api.v1.expiry_alerts import router as expiry_alerts_router
from app.api.v1.health import router as health_router
from app.api.v1.important_dates import router as important_dates_router
from app.api.v1.inspections import router as inspections_router
from app.api.v1.payments import router as payments_router
from app.api.v1.products import router as products_router
from app.api.v1.purchases import router as purchases_router
from app.api.v1.replenishment import router as replenishment_router
from app.api.v1.sales import router as sales_router
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
    app.include_router(baskets_router, prefix="/api/v1")
    app.include_router(customers_router, prefix="/api/v1")
    app.include_router(sales_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(inspections_router, prefix="/api/v1")
    app.include_router(purchases_router, prefix="/api/v1")
    app.include_router(batches_router, prefix="/api/v1")
    app.include_router(expiry_alerts_router, prefix="/api/v1")
    app.include_router(replenishment_router, prefix="/api/v1")
    app.include_router(important_dates_router, prefix="/api/v1")
    register_error_handlers(app)

    return app


app = create_application()
