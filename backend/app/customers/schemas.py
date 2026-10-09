import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.customers.models import CustomerStatus


def normalize_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        raise ValueError("O telefone é obrigatório.")
    return digits


def normalize_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", cleaned) is None:
        raise ValueError("Informe um e-mail válido.")
    return cleaned


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("O nome do cliente é obrigatório.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        return normalize_email(value)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CustomerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("O nome do cliente é obrigatório.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_phone(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        return normalize_email(value)

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def require_editable_field(self) -> "CustomerUpdate":
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo do cliente.")
        if any(
            field in self.model_fields_set and getattr(self, field) is None
            for field in ("name", "phone")
        ):
            raise ValueError("Nome e telefone não podem ser nulos.")
        return self


class CustomerStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CustomerStatus


class CustomerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime
    warning: Optional[dict[str, str]] = None
