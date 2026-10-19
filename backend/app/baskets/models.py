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
    __table_args__ = (
        CheckConstraint("price IS NULL OR price >= 0", name="ck_basket_templates_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal | None] = mapped_column(
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


