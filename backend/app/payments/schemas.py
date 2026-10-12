from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


VALID_PAYMENT_METHODS = ("PIX", "CARTAO")


class PaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal
    method: str
    idempotency_key: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero.")
        if not value.is_finite():
            raise ValueError("O valor do pagamento deve ser um valor numérico válido.")
        if value.as_tuple().exponent < -2:
            raise ValueError("O valor do pagamento deve ter no máximo duas casas decimais.")
        return value.quantize(Decimal("0.01"))

    @field_validator("method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        value = value.strip().upper()
        if value not in VALID_PAYMENT_METHODS:
            raise ValueError(
                f"Método de pagamento inválido. Use um de: {', '.join(VALID_PAYMENT_METHODS)}"
            )
        return value

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("A chave de idempotência é obrigatória.")
        return value


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    amount: Decimal
    method: str
    idempotency_key: str
    created_at: datetime


class PaymentTotalRead(BaseModel):
    sale_id: int
    total_paid: Decimal
    sale_total: Decimal
    payment_percentage: Decimal
