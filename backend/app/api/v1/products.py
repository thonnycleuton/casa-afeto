from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.inventory import service as inventory_service
from app.products.models import MovementType, Product
from app.products.schemas import (
    AdjustmentRequest,
    AvailabilityRead,
    BalanceRead,
    InventoryEntryRequest,
    MovementRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    QuantityRequest,
)
from app.products import service as product_service

router = APIRouter(prefix="/products", tags=["products", "inventory"])


def _product_response(db: Session, product: Product) -> ProductRead:
    balances = inventory_service.product_balances(db, [product])
    avg_costs = inventory_service.product_average_costs(db, [product])
    return ProductRead(
        id=product.id,
        name=product.name,
        base_unit=product.base_unit,
        reference_price=product.reference_price,
        commercial_conversion_factor=product.commercial_conversion_factor,
        active=product.active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        inventory_balance=balances[product.id],
        average_cost=avg_costs.get(product.id),
    )


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate, db: Session = Depends(get_db)
) -> ProductRead:
    product = product_service.create_product(db, payload)
    return _product_response(db, product)


@router.get("", response_model=list[ProductRead])
def list_products(
    search: Optional[str] = Query(default=None), db: Session = Depends(get_db)
) -> list[ProductRead]:
    products = product_service.list_products(db, search)
    balances = inventory_service.product_balances(db, products)
    avg_costs = inventory_service.product_average_costs(db, products)
    return [
        ProductRead(
            id=product.id,
            name=product.name,
            base_unit=product.base_unit,
            reference_price=product.reference_price,
            commercial_conversion_factor=product.commercial_conversion_factor,
            active=product.active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            inventory_balance=balances[product.id],
            average_cost=avg_costs.get(product.id),
        )
        for product in products
    ]



@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)
) -> ProductRead:
    return _product_response(
        db, product_service.update_product(db, product_id, payload)
    )


@router.post("/{product_id}/activate", response_model=ProductRead)
def activate_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    return _product_response(
        db, product_service.set_product_active(db, product_id, True)
    )


@router.post("/{product_id}/deactivate", response_model=ProductRead)
def deactivate_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    return _product_response(
        db, product_service.set_product_active(db, product_id, False)
    )


@router.get("/{product_id}/inventory/balance", response_model=BalanceRead)
def get_inventory_balance(
    product_id: int, db: Session = Depends(get_db)
) -> BalanceRead:
    return inventory_service.product_balance(db, product_id)


@router.post(
    "/{product_id}/inventory/entries",
    response_model=MovementRead,
    status_code=status.HTTP_201_CREATED,
)
def add_inventory_entry(
    product_id: int, payload: InventoryEntryRequest, db: Session = Depends(get_db)
) -> MovementRead:
    return inventory_service.create_movement(
        db,
        product_id,
        payload.quantity,
        MovementType.ENTRY,
        unit_cost=payload.unit_cost,
    )



@router.post(
    "/{product_id}/inventory/adjustments",
    response_model=MovementRead,
    status_code=status.HTTP_201_CREATED,
)
def adjust_inventory(
    product_id: int, payload: AdjustmentRequest, db: Session = Depends(get_db)
) -> MovementRead:
    return inventory_service.create_movement(
        db, product_id, payload.quantity, MovementType.ADJUSTMENT
    )


@router.get("/{product_id}/inventory/movements", response_model=list[MovementRead])
def get_inventory_history(
    product_id: int, db: Session = Depends(get_db)
) -> list[MovementRead]:
    return inventory_service.inventory_history(db, product_id)


@router.post(
    "/{product_id}/inventory/availability", response_model=AvailabilityRead
)
def check_inventory_availability(
    product_id: int,
    payload: QuantityRequest,
    db: Session = Depends(get_db),
) -> AvailabilityRead:
    return inventory_service.check_availability(db, product_id, payload.quantity)
