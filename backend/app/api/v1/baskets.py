from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.baskets import service
from app.baskets.schemas import (
    BasketCreate,
    BasketItemAdd,
    BasketItemQuantity,
    BasketItemReplace,
    BasketRead,
    BasketTemplateCreate,
    BasketTemplateRead,
    BasketTemplateUpdate,
    BasketUpdate,
)
from app.core.database import get_db

router = APIRouter()
templates_router = APIRouter(prefix="/basket-templates", tags=["basket-templates"])
baskets_router = APIRouter(prefix="/baskets", tags=["baskets"])


@templates_router.post(
    "", response_model=BasketTemplateRead, status_code=status.HTTP_201_CREATED
)
def create_template(
    payload: BasketTemplateCreate, db: Session = Depends(get_db)
) -> BasketTemplateRead:
    template = service.create_template(
        db, payload.name, payload.items, price=payload.price
    )
    return service.template_read(db, template)


@templates_router.get("", response_model=list[BasketTemplateRead])
def list_templates(db: Session = Depends(get_db)) -> list[BasketTemplateRead]:
    return [
        service.template_read(db, template)
        for template in service.list_templates(db)
    ]


@templates_router.get("/{template_id}", response_model=BasketTemplateRead)
def get_template(
    template_id: int, db: Session = Depends(get_db)
) -> BasketTemplateRead:
    return service.template_read(db, service.get_template(db, template_id))


@templates_router.patch("/{template_id}", response_model=BasketTemplateRead)
def update_template(
    template_id: int,
    payload: BasketTemplateUpdate,
    db: Session = Depends(get_db),
) -> BasketTemplateRead:
    template = service.update_template(
        db,
        template_id,
        name=payload.name,
        price=payload.price,
        update_price="price" in payload.model_fields_set,
    )
    return service.template_read(db, template)


@templates_router.post("/{template_id}/activate", response_model=BasketTemplateRead)
def activate_template(
    template_id: int, db: Session = Depends(get_db)
) -> BasketTemplateRead:
    template = service.set_template_active(db, template_id, True)
    return service.template_read(db, template)


@templates_router.post("/{template_id}/deactivate", response_model=BasketTemplateRead)
def deactivate_template(
    template_id: int, db: Session = Depends(get_db)
) -> BasketTemplateRead:
    template = service.set_template_active(db, template_id, False)
    return service.template_read(db, template)


@templates_router.post(
    "/{template_id}/items", response_model=BasketTemplateRead
)
def add_template_item(
    template_id: int, payload: BasketItemAdd, db: Session = Depends(get_db)
) -> BasketTemplateRead:
    template = service.add_template_item(
        db, template_id, payload.product_id, payload.quantity
    )
    return service.template_read(db, template)


@templates_router.patch(
    "/{template_id}/items/{product_id}", response_model=BasketTemplateRead
)
def update_template_item(
    template_id: int,
    product_id: int,
    payload: BasketItemQuantity,
    db: Session = Depends(get_db),
) -> BasketTemplateRead:
    template = service.update_template_item(
        db, template_id, product_id, payload.quantity
    )
    return service.template_read(db, template)


@templates_router.delete(
    "/{template_id}/items/{product_id}", response_model=BasketTemplateRead
)
def remove_template_item(
    template_id: int, product_id: int, db: Session = Depends(get_db)
) -> BasketTemplateRead:
    template = service.remove_template_item(db, template_id, product_id)
    return service.template_read(db, template)


@templates_router.post(
    "/{template_id}/items/{product_id}/replace", response_model=BasketTemplateRead
)
def replace_template_item(
    template_id: int,
    product_id: int,
    payload: BasketItemReplace,
    db: Session = Depends(get_db),
) -> BasketTemplateRead:
    template = service.replace_template_item(
        db, template_id, product_id, payload.product_id
    )
    return service.template_read(db, template)


@baskets_router.post("", response_model=BasketRead, status_code=status.HTTP_201_CREATED)
def create_basket(
    payload: BasketCreate, db: Session = Depends(get_db)
) -> BasketRead:
    basket = service.create_basket(
        db, payload.name, payload.template_id, payload.items
    )
    return service.basket_read(db, basket)


@baskets_router.get("", response_model=list[BasketRead])
def list_baskets(db: Session = Depends(get_db)) -> list[BasketRead]:
    return [service.basket_read(db, basket) for basket in service.list_baskets(db)]


@baskets_router.get("/{basket_id}", response_model=BasketRead)
def get_basket(basket_id: int, db: Session = Depends(get_db)) -> BasketRead:
    return service.basket_read(db, service.get_basket(db, basket_id))


@baskets_router.patch("/{basket_id}", response_model=BasketRead)
def update_basket(
    basket_id: int, payload: BasketUpdate, db: Session = Depends(get_db)
) -> BasketRead:
    basket = service.update_basket(db, basket_id, payload.name)
    return service.basket_read(db, basket)


@baskets_router.post("/{basket_id}/items", response_model=BasketRead)
def add_basket_item(
    basket_id: int, payload: BasketItemAdd, db: Session = Depends(get_db)
) -> BasketRead:
    basket = service.add_basket_item(
        db, basket_id, payload.product_id, payload.quantity
    )
    return service.basket_read(db, basket)


@baskets_router.patch(
    "/{basket_id}/items/{product_id}", response_model=BasketRead
)
def update_basket_item(
    basket_id: int,
    product_id: int,
    payload: BasketItemQuantity,
    db: Session = Depends(get_db),
) -> BasketRead:
    basket = service.update_basket_item(db, basket_id, product_id, payload.quantity)
    return service.basket_read(db, basket)


@baskets_router.delete(
    "/{basket_id}/items/{product_id}", response_model=BasketRead
)
def remove_basket_item(
    basket_id: int, product_id: int, db: Session = Depends(get_db)
) -> BasketRead:
    basket = service.remove_basket_item(db, basket_id, product_id)
    return service.basket_read(db, basket)


@baskets_router.post(
    "/{basket_id}/items/{product_id}/replace", response_model=BasketRead
)
def replace_basket_item(
    basket_id: int,
    product_id: int,
    payload: BasketItemReplace,
    db: Session = Depends(get_db),
) -> BasketRead:
    basket = service.replace_basket_item(
        db, basket_id, product_id, payload.product_id
    )
    return service.basket_read(db, basket)


router.include_router(templates_router)
router.include_router(baskets_router)
