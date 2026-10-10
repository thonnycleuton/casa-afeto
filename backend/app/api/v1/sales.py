from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.sales.models import Sale, SaleBasket
from app.sales.schemas import (
    SaleBasketAdd,
    SaleBasketCompositionUpdate,
    SaleBasketItemRead,
    SaleBasketPriceUpdate,
    SaleBasketRead,
    SaleBasketUpdate,
    SaleCompositionHistoryRead,
    SaleCreate,
    SaleDeliveryHistoryRead,
    SaleDeliveryPayload,
    SaleRead,
    SaleReopenHistoryRead,
    SaleReopenPayload,
)
from app.sales.service import (
    add_basket_to_sale,
    cancel_sale,
    confirm_sale,
    create_sale,
    deliver_basket,
    get_sale,
    list_sales,
    mark_basket_prepared,
    remove_basket_from_sale,
    reopen_sale,
    start_preparation,
    update_basket_composition,
    update_basket_delivery,
    update_basket_price,
)

router = APIRouter(prefix="/sales", tags=["sales"])


def _sale_basket_response(basket: SaleBasket) -> SaleBasketRead:
    return SaleBasketRead(
        id=basket.id,
        sale_id=basket.sale_id,
        name=basket.name,
        origin_template_id=basket.origin_template_id,
        price=basket.price,
        recipient_name=basket.recipient_name,
        delivery_address=basket.delivery_address,
        delivery_date=basket.delivery_date,
        delivery_time=basket.delivery_time,
        is_prepared=basket.is_prepared,
        is_delivered=basket.is_delivered,
        created_at=basket.created_at,
        updated_at=basket.updated_at,
        items=[
            SaleBasketItemRead(
                id=it.id,
                product_id=it.product_id,
                product_name=it.product.name,
                product_unit=(
                    it.product.base_unit.value
                    if hasattr(it.product.base_unit, "value")
                    else str(it.product.base_unit)
                ),
                quantity=it.quantity,
            )
            for it in basket.items
        ],
        composition_histories=[
            SaleCompositionHistoryRead.model_validate(h, from_attributes=True)
            for h in basket.composition_histories
        ],
        delivery_histories=[
            SaleDeliveryHistoryRead.model_validate(h, from_attributes=True)
            for h in basket.delivery_histories
        ],
    )


def _sale_response(sale: Sale) -> SaleRead:
    return SaleRead(
        id=sale.id,
        customer_id=sale.customer_id,
        customer_name=sale.customer.name,
        customer_phone=sale.customer.phone,
        status=sale.status,
        total=sale.total,
        created_at=sale.created_at,
        updated_at=sale.updated_at,
        baskets=[_sale_basket_response(b) for b in sale.baskets],
        reopen_histories=[
            SaleReopenHistoryRead.model_validate(h, from_attributes=True)
            for h in sale.reopen_histories
        ],
    )


@router.get("", response_model=list[SaleRead])
def list_sales_records(
    status: str | None = Query(default=None),
    customer_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
    db: Session = Depends(get_db),
) -> list[SaleRead]:
    sales, _ = list_sales(
        db, status=status, customer_id=customer_id, page=page, page_size=page_size
    )
    return [_sale_response(sale) for sale in sales]


@router.post("", response_model=SaleRead, status_code=status.HTTP_201_CREATED)
def create_sale_record(
    payload: SaleCreate, db: Session = Depends(get_db)
) -> SaleRead:
    sale = create_sale(db, payload)
    return _sale_response(sale)


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale_record(sale_id: int, db: Session = Depends(get_db)) -> SaleRead:
    return _sale_response(get_sale(db, sale_id))


@router.post("/{sale_id}/baskets", response_model=SaleBasketRead, status_code=status.HTTP_201_CREATED)
def add_basket_to_sale_record(
    sale_id: int, payload: SaleBasketAdd, db: Session = Depends(get_db)
) -> SaleBasketRead:
    basket = add_basket_to_sale(db, sale_id, payload)
    return _sale_basket_response(basket)


@router.delete(
    "/{sale_id}/baskets/{basket_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def remove_basket_from_sale_record(
    sale_id: int, basket_id: int, db: Session = Depends(get_db)
) -> Response:
    remove_basket_from_sale(db, sale_id, basket_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{sale_id}/baskets/{basket_id}/delivery", response_model=SaleBasketRead)
def update_basket_delivery_record(
    sale_id: int,
    basket_id: int,
    payload: SaleBasketUpdate,
    db: Session = Depends(get_db),
) -> SaleBasketRead:
    basket = update_basket_delivery(db, sale_id, basket_id, payload)
    return _sale_basket_response(basket)


@router.put("/{sale_id}/baskets/{basket_id}/price", response_model=SaleBasketRead)
def update_basket_price_record(
    sale_id: int,
    basket_id: int,
    payload: SaleBasketPriceUpdate,
    db: Session = Depends(get_db),
) -> SaleBasketRead:
    basket = update_basket_price(db, sale_id, basket_id, payload.price)
    return _sale_basket_response(basket)


@router.put("/{sale_id}/baskets/{basket_id}/composition", response_model=SaleBasketRead)
def update_basket_composition_record(
    sale_id: int,
    basket_id: int,
    payload: SaleBasketCompositionUpdate,
    db: Session = Depends(get_db),
) -> SaleBasketRead:
    basket = update_basket_composition(db, sale_id, basket_id, payload)
    return _sale_basket_response(basket)


@router.post("/{sale_id}/confirm", response_model=SaleRead)
def confirm_sale_record(sale_id: int, db: Session = Depends(get_db)) -> SaleRead:
    sale = confirm_sale(db, sale_id)
    return _sale_response(sale)


@router.post("/{sale_id}/start-preparation", response_model=SaleRead)
def start_preparation_record(sale_id: int, db: Session = Depends(get_db)) -> SaleRead:
    sale = start_preparation(db, sale_id)
    return _sale_response(sale)


@router.post("/{sale_id}/baskets/{basket_id}/prepare", response_model=SaleBasketRead)
def mark_basket_prepared_record(
    sale_id: int, basket_id: int, db: Session = Depends(get_db)
) -> SaleBasketRead:
    basket = mark_basket_prepared(db, sale_id, basket_id)
    return _sale_basket_response(basket)


@router.post("/{sale_id}/reopen", response_model=SaleRead)
def reopen_sale_record(
    sale_id: int, payload: SaleReopenPayload, db: Session = Depends(get_db)
) -> SaleRead:
    sale = reopen_sale(db, sale_id, payload)
    return _sale_response(sale)


@router.post("/{sale_id}/baskets/{basket_id}/deliver", response_model=SaleBasketRead)
def deliver_basket_record(
    sale_id: int,
    basket_id: int,
    payload: SaleDeliveryPayload,
    db: Session = Depends(get_db),
) -> SaleBasketRead:
    basket = deliver_basket(db, sale_id, basket_id, payload)
    return _sale_basket_response(basket)


@router.post("/{sale_id}/cancel", response_model=SaleRead)
def cancel_sale_record(sale_id: int, db: Session = Depends(get_db)) -> SaleRead:
    sale = cancel_sale(db, sale_id)
    return _sale_response(sale)
