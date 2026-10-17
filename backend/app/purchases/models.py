from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Numeric

from app.core.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    items: Mapped[list["PurchaseItem"]] = relationship(
        back_populates="purchase", passive_deletes=True
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

    purchase: Mapped[Purchase] = relationship(back_populates="items")
