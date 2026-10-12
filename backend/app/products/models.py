from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
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


class BaseUnit(StrEnum):
    UN = "UN"
    KG = "KG"
    G = "G"
    L = "L"
    ML = "ML"


class MovementType(StrEnum):
    ENTRY = "ENTRY"
    ADJUSTMENT = "ADJUSTMENT"
    OUTPUT = "OUTPUT"


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "base_unit IN ('UN', 'KG', 'G', 'L', 'ML')",
            name="ck_products_base_unit",
        ),
        CheckConstraint(
            "reference_price IS NULL OR reference_price >= 0",
            name="ck_products_reference_price_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    base_unit: Mapped[str] = mapped_column(String(2), nullable=False)
    reference_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=True
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="product", passive_deletes=True
    )


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint(
            "type IN ('ENTRY', 'ADJUSTMENT', 'OUTPUT')",
            name="ck_inventory_movements_type",
        ),
        CheckConstraint(
            "(type = 'ENTRY' AND quantity > 0) OR "
            "(type = 'ADJUSTMENT' AND quantity <> 0) OR "
            "(type = 'OUTPUT' AND quantity < 0)",
            name="ck_inventory_movements_quantity",
        ),
        CheckConstraint(
            "unit_cost IS NULL OR unit_cost >= 0",
            name="ck_inventory_movements_unit_cost_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True), nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=True
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    sale_id: Mapped[int | None] = mapped_column(
        ForeignKey("sales.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    product: Mapped[Product] = relationship(back_populates="movements")
