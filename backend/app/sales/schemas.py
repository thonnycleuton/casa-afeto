from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

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


def _validate_operator_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("A identificação textual do operador é obrigatória.")
    return cleaned


class SaleBasketItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int
    quantity: PositiveQuantity


class SaleBasketItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    product_unit: str
    quantity: Decimal


class SaleCompositionHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_basket_id: int
    previous_items: list[dict[str, Any]]
    new_items: list[dict[str, Any]]
    operator_name: str
    created_at: datetime


class SaleDeliveryHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_basket_id: int
    operator_name: str
    delivered_at: datetime


class SaleReopenHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    reason: str
    operator_name: str
    created_at: datetime


class SaleBasketAdd(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: int
    recipient_name: str | None = None
    delivery_address: str | None = None
    delivery_date: date | None = None
    delivery_time: str | None = None
    price: Decimal | None = None

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: Decimal | None) -> Decimal | None:
        return _validate_price(value)


class SaleBasketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipient_name: str | None = None
    delivery_address: str | None = None
    delivery_date: date | None = None
    delivery_time: str | None = None


class SaleBasketPriceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    price: Decimal

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: Decimal) -> Decimal:
        validated = _validate_price(value)
        if validated is None:
            raise ValueError("O preço é obrigatório.")
        return validated


class SaleBasketCompositionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SaleBasketItemInput]
    operator_name: str = ""
    confirmed_warning: bool = False


class SaleBasketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    name: str
    origin_template_id: int | None = None
    price: Decimal
    recipient_name: str | None = None
    delivery_address: str | None = None
    delivery_date: date | None = None
    delivery_time: str | None = None
    is_prepared: bool
    is_delivered: bool
    created_at: datetime
    updated_at: datetime
    items: list[SaleBasketItemRead] = Field(default_factory=list)
    composition_histories: list[SaleCompositionHistoryRead] = Field(default_factory=list)
    delivery_histories: list[SaleDeliveryHistoryRead] = Field(default_factory=list)


class SaleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: int
    baskets: list[SaleBasketAdd] = Field(min_length=1)


class SaleReopenPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str
    operator_name: str

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A justificativa é obrigatória para reabrir a venda.")
        return cleaned

    @field_validator("operator_name")
    @classmethod
    def validate_operator(cls, value: str) -> str:
        return _validate_operator_name(value)


class SaleDeliveryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operator_name: str

    @field_validator("operator_name")
    @classmethod
    def validate_operator(cls, value: str) -> str:
        return _validate_operator_name(value)


class SaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer_name: str
    customer_phone: str
    status: str
    total: Decimal
    created_at: datetime
    updated_at: datetime
    baskets: list[SaleBasketRead] = Field(default_factory=list)
    reopen_histories: list[SaleReopenHistoryRead] = Field(default_factory=list)
