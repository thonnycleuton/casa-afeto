from __future__ import annotations

from datetime import date as DateValue
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.important_dates.models import ImportantDateStatus

MONTH_DAY_LIMITS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class ImportantDateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    recurring: bool = False
    day: Optional[int] = None
    month: Optional[int] = None
    date: Optional[DateValue] = None

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A descrição da data importante é obrigatória.")
        return cleaned

    @field_validator("day")
    @classmethod
    def validate_day(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 1 or value > 31:
            raise ValueError("O dia deve estar entre 1 e 31.")
        return value

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 1 or value > 12:
            raise ValueError("O mês deve estar entre 1 e 12.")
        return value

    @model_validator(mode="after")
    def validate_payload(self) -> "ImportantDateCreate":
        if self.recurring:
            if self.day is None or self.month is None:
                raise ValueError("Para datas recorrentes informe dia e mês.")
            if self.date is not None:
                raise ValueError("Datas recorrentes não aceitam data completa.")
            if self.day > MONTH_DAY_LIMITS[self.month - 1]:
                raise ValueError("O dia informado não existe no mês selecionado.")
            return self
        if self.date is None:
            raise ValueError("Para datas não recorrentes informe a data completa.")
        if self.day is not None or self.month is not None:
            raise ValueError("Datas não recorrentes não aceitam dia e mês separados.")
        return self


class ImportantDateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: Optional[str] = None
    recurring: bool
    day: Optional[int] = None
    month: Optional[int] = None
    date: Optional[DateValue] = None

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A descrição da data importante é obrigatória.")
        return cleaned

    @field_validator("day")
    @classmethod
    def validate_day(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 1 or value > 31:
            raise ValueError("O dia deve estar entre 1 e 31.")
        return value

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: Optional[int]) -> Optional[int]:
        if value is None:
            return None
        if value < 1 or value > 12:
            raise ValueError("O mês deve estar entre 1 e 12.")
        return value

    @model_validator(mode="after")
    def validate_payload(self) -> "ImportantDateUpdate":
        if self.recurring:
            if self.day is None or self.month is None:
                raise ValueError("Para datas recorrentes informe dia e mês.")
            if self.date is not None:
                raise ValueError("Datas recorrentes não aceitam data completa.")
            if self.day > MONTH_DAY_LIMITS[self.month - 1]:
                raise ValueError("O dia informado não existe no mês selecionado.")
        else:
            if self.date is None:
                raise ValueError("Para datas não recorrentes informe a data completa.")
            if self.day is not None or self.month is not None:
                raise ValueError("Datas não recorrentes não aceitam dia e mês separados.")
        return self


class ImportantDateStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ImportantDateStatus


class ImportantDateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    customer_id: int
    description: str
    recurring: bool
    day: Optional[int] = None
    month: Optional[int] = None
    date: Optional[DateValue] = None
    status: ImportantDateStatus
    created_at: datetime
    updated_at: datetime


class UpcomingDateRead(BaseModel):
    """Schema de resposta para datas próximas (M10)."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    customer_id: int
    customer_name: str
    description: str
    recurring: bool
    next_occurrence: DateValue
    status: ImportantDateStatus


class UpcomingDatesListRead(BaseModel):
    """Schema de resposta para a lista de datas próximas (M10)."""

    items: list[UpcomingDateRead]
    total: int
