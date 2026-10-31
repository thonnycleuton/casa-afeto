import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.baskets import service
from app.baskets.schemas import (
    BasketItemAdd,
    BasketItemQuantity,
    BasketItemReplace,
    BasketTemplateCreate,
    BasketTemplateRead,
    BasketTemplateUpdate,
)
from app.core.database import get_db

router = APIRouter()
templates_router = APIRouter(prefix="/basket-templates", tags=["basket-templates"])


@templates_router.post(
    "", response_model=BasketTemplateRead, status_code=status.HTTP_201_CREATED
)
def create_template(
    payload: BasketTemplateCreate, db: Session = Depends(get_db)
) -> BasketTemplateRead:
    template = service.create_template(
        db, payload.name, payload.items, price=payload.price, image_url=payload.image_url
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
        image_url=payload.image_url if "image_url" in payload.model_fields_set else None,
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


@templates_router.post(
    "/{template_id}/image",
    response_model=BasketTemplateRead,
)
async def upload_template_image(
    template_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> BasketTemplateRead:
    """Upload an image for a basket template."""
    # Validate file type
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de arquivo não permitido. Use JPEG, PNG, WebP ou GIF.",
        )

    # Read and validate file size
    content = await file.read()
    if len(content) > settings.MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Imagem muito grande. Tamanho máximo: 5 MB.",
        )

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"

    # Ensure upload directory exists
    upload_dir = settings.entity_upload_path("basket-templates")
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename

    # Save file
    with open(filepath, "wb") as f:
        f.write(content)

    # Update template with image URL
    template = service.update_template(
        db, template_id, image_url=f"/api/v1/basket-templates/uploads/{filename}"
    )
    return service.template_read(db, template)


router.include_router(templates_router)
