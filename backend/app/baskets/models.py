from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Numeric

from app.core.database import Base
from app.products.models import Product


class BasketTemplate(Base):
    __tablename__ = "basket_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
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
    items: Mapped[list["BasketTemplateItem"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BasketTemplateItem.id",
    )


class BasketTemplateItem(Base):
    __tablename__ = "basket_template_items"
    __table_args__ = (
        UniqueConstraint("template_id", "product_id", name="uq_basket_template_items_product"),
        CheckConstraint("quantity > 0", name="ck_basket_template_items_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("basket_templates.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True), nullable=False)
    template: Mapped[BasketTemplate] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Basket(Base):
    __tablename__ = "baskets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    template_id: Mapped[int | None] = mapped_column(
        ForeignKey("basket_templates.id", ondelete="RESTRICT"), nullable=True, index=True
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
    items: Mapped[list["BasketItem"]] = relationship(
        back_populates="basket",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BasketItem.id",
    )
    template: Mapped[BasketTemplate | None] = relationship()


class BasketItem(Base):
    __tablename__ = "basket_items"
    __table_args__ = (
        UniqueConstraint("basket_id", "product_id", name="uq_basket_items_product"),
        CheckConstraint("quantity > 0", name="ck_basket_items_quantity_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    basket_id: Mapped[int] = mapped_column(
        ForeignKey("baskets.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True), nullable=False)
    basket: Mapped[Basket] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()
