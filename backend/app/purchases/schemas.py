from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class CreatePurchaseItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int
    commercial_unit: Optional[str] = None
    conversion_factor: Decimal
    commercial_quantity: Decimal
    commercial_unit_price: Decimal

    @field_validator("commercial_unit")
    @classmethod
    def validate_commercial_unit(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        return value

    @field_validator("conversion_factor")
    @classmethod
    def validate_conversion_factor(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("O fator de conversão deve ser maior que zero.")
        if not value.is_finite():
            raise ValueError("O fator de conversão deve ser um valor numérico válido.")
        return value

    @field_validator("commercial_quantity")
    @classmethod
    def validate_commercial_quantity(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("A quantidade comercial deve ser maior que zero.")
        if not value.is_finite():
            raise ValueError("A quantidade comercial deve ser um valor numérico válido.")
        return value

    @field_validator("commercial_unit_price")
    @classmethod
    def validate_commercial_unit_price(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("O preço de aquisição não pode ser negativo.")
        if not value.is_finite():
            raise ValueError("O preço de aquisição deve ser um valor numérico válido.")
        if value.as_tuple().exponent < -2:
            raise ValueError("O preço de aquisição deve ter no máximo duas casas decimais.")
        return value.quantize(Decimal("0.01"))


class CreatePurchase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    purchased_at: Optional[datetime] = None
    items: list[CreatePurchaseItem]

    @field_validator("items")
    @classmethod
    def validate_items(cls, value: list[CreatePurchaseItem]) -> list[CreatePurchaseItem]:
        if not value:
            raise ValueError("A compra deve conter pelo menos um item.")
        return value


class PurchaseItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    base_unit: str
    commercial_unit: Optional[str] = None
    conversion_factor: Decimal
    commercial_quantity: Decimal
    commercial_unit_price: Decimal


class PurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchased_at: datetime
    items: list[PurchaseItemRead] = []


class ListPurchasesFilter(BaseModel):
    purchased_from: Optional[datetime] = None
    purchased_until: Optional[datetime] = None
