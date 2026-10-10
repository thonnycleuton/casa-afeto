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


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    base_unit: BaseUnit

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("O nome do produto é obrigatório.")
        return value


class ProductUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    base_unit: Optional[BaseUnit] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("O nome do produto é obrigatório.")
        return value

    @model_validator(mode="after")
    def require_editable_field(self) -> "ProductUpdate":
        if self.name is None and self.base_unit is None:
            raise ValueError("Informe ao menos um campo do produto.")
        return self


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_unit: BaseUnit
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
