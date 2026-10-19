from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.products.models import BaseUnit, MovementType


def _validate_reference_price(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if not value.is_finite():
        raise ValueError("O preço de referência deve ser um valor numérico válido.")
    if value < 0:
        raise ValueError("O preço de referência não pode ser negativo.")
    if value.as_tuple().exponent < -2:
        raise ValueError("O preço de referência deve ter no máximo duas casas decimais.")
    return value.quantize(Decimal("0.01"))


def _validate_commercial_conversion_factor(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    if not value.is_finite():
        raise ValueError("O fator de conversão deve ser um valor numérico válido.")
    if value <= 0:
        raise ValueError("O fator de conversão deve ser maior que zero.")
    if value.as_tuple().exponent < -2:
        raise ValueError("O fator de conversão deve ter no máximo duas casas decimais.")
    return value.quantize(Decimal("0.01"))


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    base_unit: BaseUnit
    reference_price: Decimal | None = None
    commercial_conversion_factor: Decimal | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome do produto é obrigatório.")
        return value

    @field_validator("reference_price")
    @classmethod
    def validate_reference_price(cls, value: Decimal | None) -> Decimal | None:
        return _validate_reference_price(value)

    @field_validator("commercial_conversion_factor")
    @classmethod
    def validate_commercial_conversion_factor(cls, value: Decimal | None) -> Decimal | None:
        return _validate_commercial_conversion_factor(value)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    base_unit: Optional[BaseUnit] = None
    reference_price: Optional[Decimal] = None
    commercial_conversion_factor: Optional[Decimal] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("O nome do produto é obrigatório.")
        return value

    @field_validator("reference_price")
    @classmethod
    def validate_reference_price(cls, value: Decimal | None) -> Decimal | None:
        return _validate_reference_price(value)

    @field_validator("commercial_conversion_factor")
    @classmethod
    def validate_commercial_conversion_factor(cls, value: Decimal | None) -> Decimal | None:
        return _validate_commercial_conversion_factor(value)

    @model_validator(mode="after")
    def require_editable_field(self) -> "ProductUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo do produto.")
        return self


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_unit: BaseUnit
    reference_price: Optional[Decimal] = None
    commercial_conversion_factor: Optional[Decimal] = None
    active: bool
    created_at: datetime
    updated_at: datetime
    inventory_balance: Decimal
    average_cost: Optional[Decimal] = None


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: Decimal
    type: MovementType
    unit_cost: Optional[Decimal] = None
    sale_id: Optional[int] = None
    purchase_id: Optional[int] = None
    created_at: datetime


class QuantityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Annotated[Decimal, Field(gt=0)]


class InventoryEntryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Annotated[Decimal, Field(gt=0)]
    unit_cost: Optional[Decimal] = None

    @field_validator("unit_cost")
    @classmethod
    def validate_unit_cost(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        if value is None:
            return None
        if not value.is_finite():
            raise ValueError("O custo unitário deve ser um valor numérico válido.")
        if value < 0:
            raise ValueError("O custo unitário não pode ser negativo.")
        if value.as_tuple().exponent < -2:
            raise ValueError("O custo unitário deve ter no máximo duas casas decimais.")
        return value.quantize(Decimal("0.01"))



class AdjustmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Decimal

    @field_validator("quantity")
    @classmethod
    def reject_zero(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("A quantidade do ajuste não pode ser zero.")
        return value


class BalanceRead(BaseModel):
    product_id: int
    quantity: Decimal
    base_unit: BaseUnit


class AvailabilityRead(BaseModel):
    product_id: int
    available: bool
    available_quantity: Decimal
    required_quantity: Decimal
    shortage: Decimal
    base_unit: BaseUnit
