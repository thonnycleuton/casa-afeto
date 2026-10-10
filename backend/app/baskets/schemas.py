from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PositiveQuantity = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


def _validate_price(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if not value.is_finite():
        raise ValueError("O preço deve ser um valor numérico válido.")
    if value < 0:
        raise ValueError("O preço não pode ser negativo.")
    if value.as_tuple().exponent < -2:
        raise ValueError("O preço deve ter no máximo duas casas decimais.")
    return value.quantize(Decimal("0.01"))


class BasketItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int
    quantity: PositiveQuantity


class BasketItemAdd(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int
    quantity: PositiveQuantity


class BasketItemQuantity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: PositiveQuantity


class BasketItemReplace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int


class BasketTemplateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    price: Decimal | None = None
    items: list[BasketItemInput] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome do template é obrigatório.")
        return value

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: Decimal | None) -> Decimal | None:
        return _validate_price(value)


class BasketTemplateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    price: Decimal | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("O nome do template é obrigatório.")
        return value

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: Decimal | None) -> Decimal | None:
        return _validate_price(value)

    @model_validator(mode="after")
    def validate_payload_not_empty(self) -> "BasketTemplateUpdate":
        if not self.model_fields_set:
            raise ValueError("Ao menos um campo deve ser informado para atualização.")
        return self


class BasketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    template_id: int | None = None
    items: list[BasketItemInput] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome da cesta é obrigatório.")
        return value

    @model_validator(mode="after")
    def reject_items_with_template(self) -> "BasketCreate":
        if self.template_id is not None and self.items:
            raise ValueError(
                "A composição da cesta é copiada do template selecionado."
            )
        return self


class BasketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome da cesta é obrigatório.")
        return value


class ProductCompositionRead(BaseModel):
    product_id: int
    product_name: str
    product_active: bool
    base_unit: str
    quantity: Decimal
    inventory_balance: Decimal
    stock_available: bool
    stock_shortage: Decimal
    unit_cost: Decimal | None = None
    total_cost: Decimal | None = None


class BasketTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    active: bool
    price: Decimal | None = None
    estimated_cost: Decimal | None = None
    suggested_price: Decimal | None = None
    has_reliable_cost: bool = False
    created_at: datetime
    updated_at: datetime
    items: list[ProductCompositionRead]


class BasketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    template_id: int | None
    estimated_cost: Decimal | None = None
    suggested_price: Decimal | None = None
    has_reliable_cost: bool = False
    created_at: datetime
    updated_at: datetime
    items: list[ProductCompositionRead]
