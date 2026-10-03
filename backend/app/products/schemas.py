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
            raise ValueError("Product name is required.")
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
            raise ValueError("Product name is required.")
        return value

    @model_validator(mode="after")
    def require_editable_field(self) -> "ProductUpdate":
        if self.name is None and self.base_unit is None:
            raise ValueError("At least one product field must be provided.")
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


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: Decimal
    type: MovementType
    created_at: datetime


class QuantityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Annotated[Decimal, Field(gt=0)]


class AdjustmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Decimal

    @field_validator("quantity")
    @classmethod
    def reject_zero(cls, value: Decimal) -> Decimal:
        if value == 0:
            raise ValueError("Adjustment quantity cannot be zero.")
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
