from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

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
    expiry_date: Optional[date] = None

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
    access_key: Optional[str] = None
    supplier_name: Optional[str] = None
    cnpj: Optional[str] = None
    invoice_number: Optional[str] = None
    items: list[CreatePurchaseItem]

    @field_validator("items")
    @classmethod
    def validate_items(cls, value: list[CreatePurchaseItem]) -> list[CreatePurchaseItem]:
        if not value:
            raise ValueError("A compra deve conter pelo menos um item.")
        return value

    @field_validator("access_key")
    @classmethod
    def validate_access_key(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if not (len(value) == 44 and all(c in "0123456789" for c in value)):
            raise ValueError("A chave de acesso deve conter exatamente 44 dígitos numéricos.")
        return value


class ItemDiscount(BaseModel):
    """Desconto informativo de um item de compra."""
    model_config = ConfigDict(extra="forbid")
    value: Optional[Decimal] = None
    nature: Optional[str] = None
    description: Optional[str] = None


class DocumentDiscountCreate(BaseModel):
    """Desconto geral do documento para criação."""
    model_config = ConfigDict(extra="forbid")
    value: Decimal
    nature: Optional[str] = None
    description: Optional[str] = None


class DocumentDiscountRead(BaseModel):
    """Desconto geral do documento para leitura."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    value: Decimal
    nature: Optional[str] = None
    description: Optional[str] = None


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
    expiry_date: Optional[date] = None
    item_discounts: Optional[list[dict[str, Any]]] = None


class PurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchased_at: datetime
    access_key: Optional[str] = None
    status: str
    supplier_name: Optional[str] = None
    cnpj: Optional[str] = None
    invoice_number: Optional[str] = None
    document_path: Optional[str] = None
    items: list[PurchaseItemRead] = []
    document_discounts: list[DocumentDiscountRead] = []


class CreateDraftItem(CreatePurchaseItem):
    """Item para rascunho — reutiliza validações de CreatePurchaseItem."""
    item_discounts: Optional[list[ItemDiscount]] = None


class CreateDraft(BaseModel):
    """Criar rascunho de compra — itens opcionais (permite lista vazia)."""
    model_config = ConfigDict(extra="forbid")

    purchased_at: Optional[datetime] = None
    access_key: Optional[str] = None
    supplier_name: Optional[str] = None
    cnpj: Optional[str] = None
    invoice_number: Optional[str] = None
    document_path: Optional[str] = None
    items: list[CreateDraftItem] = []
    document_discounts: Optional[list[DocumentDiscountCreate]] = None

    @field_validator("access_key")
    @classmethod
    def validate_access_key(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if not (len(value) == 44 and all(c in "0123456789" for c in value)):
            raise ValueError("A chave de acesso deve conter exatamente 44 dígitos numéricos.")
        return value


class UpdateDraftItem(CreatePurchaseItem):
    """Item para edição — reutiliza validações de CreatePurchaseItem."""
    item_discounts: Optional[list[ItemDiscount]] = None


class UpdateDraft(BaseModel):
    """Editar compra — todos os campos opcionais.
    
    Usa model_fields_set para diferenciar campos omitidos de campos explicitamente None.
    document_path é excluído — definido exclusivamente pelo backend (OCR).
    """
    model_config = ConfigDict(extra="forbid")

    purchased_at: Optional[datetime] = None
    supplier_name: Optional[str] = None
    cnpj: Optional[str] = None
    invoice_number: Optional[str] = None
    items: Optional[list[UpdateDraftItem]] = None
    document_discounts: Optional[list[DocumentDiscountCreate]] = None


class ListPurchasesFilter(BaseModel):
    purchased_from: Optional[datetime] = None
    purchased_until: Optional[datetime] = None
