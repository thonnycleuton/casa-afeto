from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class InspectionRecordPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inspected_quantity: Decimal
    reusable_quantity: Decimal
    operator_name: str

    @field_validator("inspected_quantity")
    @classmethod
    def validate_inspected(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("A quantidade inspecionada não pode ser negativa.")
        return value

    @field_validator("reusable_quantity")
    @classmethod
    def validate_reusable(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("A quantidade reutilizável não pode ser negativa.")
        return value

    @field_validator("operator_name")
    @classmethod
    def validate_operator(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A identificação do operador é obrigatória.")
        return value

    @field_validator("reusable_quantity")
    @classmethod
    def reusable_le_inspected(cls, value: Decimal, info) -> Decimal:
        if hasattr(info, 'data') and 'inspected_quantity' in info.data:
            if value > info.data['inspected_quantity']:
                raise ValueError(
                    "A quantidade reutilizável não pode exceder a quantidade inspecionada."
                )
        return value


class ReintegrationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Decimal
    operator_name: str

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("A quantidade a reintegrar deve ser maior que zero.")
        return value

    @field_validator("operator_name")
    @classmethod
    def validate_operator(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A identificação do operador é obrigatória.")
        return value


class InspectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    product_id: int
    consumed_quantity: Decimal
    inspected_quantity: Decimal
    reusable_quantity: Decimal
    operator_name: str
    inspected_at: datetime | None
    reintegrated_quantity: Decimal
    reintegrated_movement_id: int | None
    status: str
