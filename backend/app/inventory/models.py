from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Numeric

from app.core.database import Base


class StockBatch(Base):
    __tablename__ = "stock_batches"
    __table_args__ = (
        CheckConstraint(
            "quantity_original > 0",
            name="ck_stock_batches_quantity_original_positive",
        ),
        CheckConstraint(
            "quantity_remaining >= 0",
            name="ck_stock_batches_quantity_remaining_non_negative",
        ),
        CheckConstraint(
            "unit_cost IS NULL OR unit_cost >= 0",
            name="ck_stock_batches_unit_cost_non_negative",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'EXHAUSTED')",
            name="ck_stock_batches_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    purchase_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    purchase_item_id: Mapped[int | None] = mapped_column(
        nullable=True
    )
    quantity_original: Mapped[Decimal] = mapped_column(
        Numeric(asdecimal=True), nullable=False
    )
    quantity_remaining: Mapped[Decimal] = mapped_column(
        Numeric(asdecimal=True), nullable=False
    )
    unit_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    expiry_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="batch", passive_deletes=True
    )
