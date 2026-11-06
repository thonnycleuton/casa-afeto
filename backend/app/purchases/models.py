from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Numeric

from app.core.database import Base


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        UniqueConstraint("access_key", name="uq_purchases_access_key"),
        CheckConstraint(
            "status IN ('DRAFT', 'CONFIRMED')",
            name="ck_purchases_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    access_key: Mapped[str | None] = mapped_column(
        String(44), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="CONFIRMED"
    )
    supplier_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    cnpj: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    invoice_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    document_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    items: Mapped[list["PurchaseItem"]] = relationship(
        back_populates="purchase", passive_deletes=True
    )
    document_discounts: Mapped[list["PurchaseDocumentDiscount"]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan", passive_deletes=True
    )


class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint(
            "conversion_factor > 0",
            name="ck_purchase_items_conversion_factor_positive",
        ),
        CheckConstraint(
            "commercial_quantity > 0",
            name="ck_purchase_items_quantity_positive",
        ),
        CheckConstraint(
            "commercial_unit_price >= 0",
            name="ck_purchase_items_price_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    commercial_unit: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    conversion_factor: Mapped[Decimal] = mapped_column(
        Numeric(asdecimal=True), nullable=False
    )
    commercial_quantity: Mapped[Decimal] = mapped_column(
        Numeric(asdecimal=True), nullable=False
    )
    commercial_unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False
    )
    expiry_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    item_discounts: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON, nullable=True, default=None
    )

    purchase: Mapped[Purchase] = relationship(back_populates="items")


class PurchaseDocumentDiscount(Base):
    __tablename__ = "purchase_document_discounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False
    )
    nature: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    purchase: Mapped[Purchase] = relationship(back_populates="document_discounts")
