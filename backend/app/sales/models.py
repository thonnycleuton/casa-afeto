from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base
from app.customers.models import Customer
from app.products.models import Product


class SaleStatus(StrEnum):
    RASCUNHO = "RASCUNHO"
    CONFIRMADA = "CONFIRMADA"
    EM_PREPARACAO = "EM PREPARAÇÃO"
    PRONTA = "PRONTA"
    ENTREGUE = "ENTREGUE"
    CANCELADA = "CANCELADA"


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'CONFIRMADA', 'EM PREPARAÇÃO', 'PRONTA', 'ENTREGUE', 'CANCELADA')",
            name="ck_sales_status",
        ),
        CheckConstraint("total >= 0", name="ck_sales_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SaleStatus.RASCUNHO.value
    )
    total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False, default=Decimal("0.00")
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

    customer: Mapped[Customer] = relationship()
    baskets: Mapped[list["SaleBasket"]] = relationship(
        back_populates="sale",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SaleBasket.id",
    )
    reopen_histories: Mapped[list["SaleReopenHistory"]] = relationship(
        back_populates="sale",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SaleReopenHistory.id",
    )


class SaleBasket(Base):
    __tablename__ = "sale_baskets"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_sale_baskets_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    origin_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("basket_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2, asdecimal=True), nullable=False
    )
    recipient_name: Mapped[str | None] = mapped_column(String, nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(String, nullable=True)
    delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivery_time: Mapped[str | None] = mapped_column(String, nullable=True)
    is_prepared: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_delivered: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
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

    sale: Mapped[Sale] = relationship(back_populates="baskets")
    items: Mapped[list["SaleBasketItem"]] = relationship(
        back_populates="sale_basket",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SaleBasketItem.id",
    )
    composition_histories: Mapped[list["SaleCompositionHistory"]] = relationship(
        back_populates="sale_basket",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SaleCompositionHistory.id",
    )
    delivery_histories: Mapped[list["SaleDeliveryHistory"]] = relationship(
        back_populates="sale_basket",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SaleDeliveryHistory.id",
    )


class SaleBasketItem(Base):
    __tablename__ = "sale_basket_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_basket_items_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_basket_id: Mapped[int] = mapped_column(
        ForeignKey("sale_baskets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True), nullable=False)

    sale_basket: Mapped[SaleBasket] = relationship(back_populates="items")
    product: Mapped[Product] = relationship()


class SaleCompositionHistory(Base):
    __tablename__ = "sale_composition_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_basket_id: Mapped[int] = mapped_column(
        ForeignKey("sale_baskets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_items: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False
    )
    new_items: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON, nullable=False
    )
    operator_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sale_basket: Mapped[SaleBasket] = relationship(back_populates="composition_histories")


class SaleReopenHistory(Base):
    __tablename__ = "sale_reopen_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String, nullable=False)
    operator_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sale: Mapped[Sale] = relationship(back_populates="reopen_histories")


class SaleDeliveryHistory(Base):
    __tablename__ = "sale_delivery_histories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_basket_id: Mapped[int] = mapped_column(
        ForeignKey("sale_baskets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    operator_name: Mapped[str] = mapped_column(String, nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sale_basket: Mapped[SaleBasket] = relationship(back_populates="delivery_histories")


class SaleStockReservation(Base):
    __tablename__ = "sale_stock_reservations"
    __table_args__ = (
        CheckConstraint("current_quantity >= 0", name="ck_reservations_current_quantity_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_reservations_reserved_quantity_non_negative"),
        CheckConstraint("consumed_quantity >= 0", name="ck_reservations_consumed_quantity_non_negative"),
        CheckConstraint("consumed_quantity <= reserved_quantity", name="ck_reservations_consumed_le_reserved"),
        CheckConstraint(
            "status IN ('ACTIVE', 'RELEASED', 'CONSUMED')",
            name="ck_reservations_status",
        ),
        UniqueConstraint("sale_id", "product_id", name="uq_reservations_sale_product"),
        Index("ix_sale_stock_reservations_sale_id", "sale_id"),
        Index("ix_sale_stock_reservations_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    current_quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True), nullable=False)
    reserved_quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True), nullable=False)
    consumed_quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SaleCancellationInspection(Base):
    __tablename__ = "sale_cancellation_inspection"
    __table_args__ = (
        CheckConstraint("consumed_quantity > 0", name="ck_inspection_consumed_positive"),
        CheckConstraint("inspected_quantity >= 0", name="ck_inspection_inspected_non_negative"),
        CheckConstraint("inspected_quantity <= consumed_quantity", name="ck_inspection_inspected_le_consumed"),
        CheckConstraint("reusable_quantity >= 0", name="ck_inspection_reusable_non_negative"),
        CheckConstraint("reusable_quantity <= inspected_quantity", name="ck_inspection_reusable_le_inspected"),
        CheckConstraint("reintegrated_quantity >= 0", name="ck_inspection_reintegrated_non_negative"),
        CheckConstraint("reintegrated_quantity <= reusable_quantity", name="ck_inspection_reintegrated_le_reusable"),
        CheckConstraint(
            "status IN ('PENDING', 'INSPECTED', 'REINTEGRATED', 'DISCARDED')",
            name="ck_inspection_status",
        ),
        UniqueConstraint("sale_id", "product_id", name="uq_inspection_sale_product"),
        Index("ix_sale_cancellation_inspection_sale_id", "sale_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    consumed_quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True), nullable=False)
    inspected_quantity: Mapped[Decimal] = mapped_column(
        Numeric(asdecimal=True), nullable=False, server_default="0"
    )
    reusable_quantity: Mapped[Decimal] = mapped_column(
        Numeric(asdecimal=True), nullable=False, server_default="0"
    )
    operator_name: Mapped[str] = mapped_column(String, nullable=False)
    inspected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reintegrated_quantity: Mapped[Decimal] = mapped_column(
        Numeric(asdecimal=True), nullable=False, server_default="0"
    )
    reintegrated_movement_id: Mapped[int | None] = mapped_column(
        ForeignKey("inventory_movements.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
