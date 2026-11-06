"""OCR schemas for M13 — Pydantic models for OCR sessions, items, and results."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class OCRDiscount(BaseModel):
    """Desconto identificado pelo Gemini (D-18, sem aplicação automática)."""

    value: Decimal | None = None
    nature: str | None = None  # "item", "grupo", "documento"
    item_id: str | None = None  # identificador estável do item extraído (UUID)
    document_level: bool = False
    description: str | None = None


class OCRItem(BaseModel):
    """Item extraído do documento pelo Gemini."""

    # Extraídos pelo Gemini
    item_id: str  # identificador estável (UUID, gerado no parsing)
    description: str | None = None
    quantity: Decimal | None = None
    commercial_unit: str | None = None
    commercial_unit_price: Decimal | None = None
    subtotal_printed: Decimal | None = None
    subtotal_calculated: Decimal | None = None
    discounts: list[OCRDiscount] = Field(default_factory=list)

    # Após matching/revisão
    product_id: int | None = None
    conversion_factor: Decimal | None = None
    expiry_date: date | None = None
    is_deleted: bool = False
    is_new_product: bool = False

    # Lotes múltiplos (D-11)
    lots: list[OCRLot] | None = None


class OCRLot(BaseModel):
    """Lote individual para divisão de item (D-11)."""

    commercial_quantity: Decimal
    commercial_unit: str | None = None
    conversion_factor: Decimal
    commercial_unit_price: Decimal
    expiry_date: date | None = None


OCRStatus = Literal["pending", "processing", "completed", "failed"]


class OCRSession(BaseModel):
    """Sessão OCR em memória (D-12)."""

    session_id: str
    status: OCRStatus
    document_total: Decimal | None = None
    purchased_at: datetime | None = None
    access_key: str | None = None
    items: list[OCRItem] = Field(default_factory=list)
    document_discounts: list[OCRDiscount] = Field(default_factory=list)
    error: str | None = None
    file_path: str | None = None
    file_mime_type: str | None = None
    model_used: str | None = None


class UploadResponse(BaseModel):
    """Resposta do endpoint de upload."""

    session_id: str
    status: OCRStatus


class StatusResponse(BaseModel):
    """Resposta do endpoint de polling de status.

    Includes three financial indicators (D-17):
    - extracted_total: sum of subtotals of all original items (including excluded).
    - launched_total: sum of subtotals of confirmed items only (None before confirmation).
    - items_without_subtotal_count: count of items without available subtotal.
    """

    session_id: str
    status: OCRStatus
    document_total: Decimal | None = None
    purchased_at: datetime | None = None
    access_key: str | None = None
    items: list[OCRItem] = Field(default_factory=list)
    document_discounts: list[OCRDiscount] = Field(default_factory=list)
    error: str | None = None
    model_used: str | None = None
    # Financial indicators (D-17)
    extracted_total: Decimal | None = None
    launched_total: Decimal | None = None
    items_without_subtotal_count: int = 0


class OCRResult(BaseModel):
    """Resultado completo da extração OCR."""

    document_total: Decimal | None = None
    purchased_at: datetime | None = None
    access_key: str | None = None
    items: list[OCRItem]
    document_discounts: list[OCRDiscount] = Field(default_factory=list)


# ─── Confirmação de importação (Etapa 2) ───────────────────────────────


class ConfirmLot(BaseModel):
    """Lote confirmado pelo operador (D-11).

    O preço unitário não é enviado pelo cliente — é calculado pelo backend
    a partir do preço do item e da proporção entre os fatores de conversão.
    """

    commercial_quantity: Decimal
    commercial_unit: str | None = None
    conversion_factor: Decimal
    expiry_date: date | None = None

    @field_validator("commercial_quantity")
    @classmethod
    def validate_commercial_quantity(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("A quantidade do lote deve ser maior que zero.")
        if not value.is_finite():
            raise ValueError("A quantidade do lote deve ser um valor numérico válido.")
        return value

    @field_validator("conversion_factor")
    @classmethod
    def validate_conversion_factor(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("O fator de conversão do lote deve ser maior que zero.")
        if not value.is_finite():
            raise ValueError("O fator de conversão do lote deve ser um valor numérico válido.")
        return value


class ConfirmedItem(BaseModel):
    """Item confirmado pelo operador para lançamento na compra."""

    item_id: str  # referencia o item original extraído (UUID)
    product_id: int
    commercial_unit: str | None = None
    conversion_factor: Decimal
    commercial_quantity: Decimal
    commercial_unit_price: Decimal
    expiry_date: date | None = None
    lots: list[ConfirmLot] | None = None

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
            raise ValueError("O preço unitário não pode ser negativo.")
        if not value.is_finite():
            raise ValueError("O preço unitário deve ser um valor numérico válido.")
        if value.as_tuple().exponent < -2:
            raise ValueError("O preço unitário deve ter no máximo duas casas decimais.")
        return value.quantize(Decimal("0.01"))


class ConfirmImportRequest(BaseModel):
    """Solicitação de confirmação de importação OCR.

    O operador envia os itens confirmados e os IDs dos itens excluídos.
    A validação de que cada item original aparece exatamente uma vez
    (sem sobreposição ou omissão) é feita pelo serviço, não pelo schema.
    """

    confirmed_items: list[ConfirmedItem]
    excluded_item_ids: list[str] = Field(default_factory=list)

    @field_validator("confirmed_items")
    @classmethod
    def validate_confirmed_items(cls, value: list[ConfirmedItem]) -> list[ConfirmedItem]:
        if not value:
            raise ValueError("Deve haver pelo menos um item confirmado.")
        item_ids = [item.item_id for item in value]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("A lista de itens confirmados não pode conter item_id duplicado.")
        return value

    @field_validator("excluded_item_ids")
    @classmethod
    def validate_excluded_item_ids(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("A lista de itens excluídos não pode conter duplicatas.")
        return value


class ConfirmImportTotals(BaseModel):
    """Totais calculados na confirmação da importação."""

    extracted_total: Decimal | None = None
    launched_total: Decimal
    items_without_subtotal_count: int = 0

    @field_validator("extracted_total")
    @classmethod
    def validate_extracted_total(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("O total extraído não pode ser negativo.")
        return value

    @field_validator("launched_total")
    @classmethod
    def validate_launched_total(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("O total lançado não pode ser negativo.")
        return value

    @field_validator("items_without_subtotal_count")
    @classmethod
    def validate_items_without_subtotal_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("A contagem de itens sem subtotal não pode ser negativa.")
        return value


class ConfirmedItemRead(BaseModel):
    """Item confirmado retornado na resposta."""

    item_id: str
    product_id: int
    commercial_unit: str | None = None
    conversion_factor: Decimal
    commercial_quantity: Decimal
    commercial_unit_price: Decimal
    expiry_date: date | None = None
    lots: list[ConfirmLot] | None = None


class ExcludedItemRead(BaseModel):
    """Item excluído retornado na resposta."""

    item_id: str
    description: str | None = None


class ConfirmImportResponse(BaseModel):
    """Resposta da confirmação de importação OCR.

    A compra criada está em estado DRAFT — o operador deve confirmá-la
    separadamente via POST /purchases/{id}/confirm para gerar ENTRY.
    """

    purchase_id: int
    purchased_at: datetime
    access_key: str | None = None
    status: str = "DRAFT"
    confirmed_items: list[ConfirmedItemRead]
    excluded_items: list[ExcludedItemRead] = Field(default_factory=list)
    totals: ConfirmImportTotals
