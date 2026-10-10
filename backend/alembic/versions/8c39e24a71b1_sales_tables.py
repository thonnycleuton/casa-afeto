"""sales_tables

Revision ID: 8c39e24a71b1
Revises: 65e00c126251
Create Date: 2026-10-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c39e24a71b1'
down_revision: Union[str, None] = '65e00c126251'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="RASCUNHO", nullable=False),
        sa.Column("total", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'CONFIRMADA', 'EM PREPARAÇÃO', 'PRONTA', 'ENTREGUE', 'CANCELADA')",
            name="ck_sales_status",
        ),
        sa.CheckConstraint("total >= 0", name="ck_sales_total_non_negative"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sales_customer_id"), "sales", ["customer_id"], unique=False)

    op.create_table(
        "sale_baskets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("origin_template_id", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("recipient_name", sa.String(), nullable=True),
        sa.Column("delivery_address", sa.String(), nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("delivery_time", sa.String(), nullable=True),
        sa.Column("is_prepared", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_delivered", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("price >= 0", name="ck_sale_baskets_price_non_negative"),
        sa.ForeignKeyConstraint(["origin_template_id"], ["basket_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_baskets_sale_id"), "sale_baskets", ["sale_id"], unique=False)
    op.create_index(op.f("ix_sale_baskets_origin_template_id"), "sale_baskets", ["origin_template_id"], unique=False)

    op.create_table(
        "sale_basket_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_basket_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_sale_basket_items_quantity_positive"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["sale_basket_id"], ["sale_baskets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_basket_items_sale_basket_id"), "sale_basket_items", ["sale_basket_id"], unique=False)
    op.create_index(op.f("ix_sale_basket_items_product_id"), "sale_basket_items", ["product_id"], unique=False)

    op.create_table(
        "sale_composition_histories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_basket_id", sa.Integer(), nullable=False),
        sa.Column("previous_items", sa.JSON(), nullable=False),
        sa.Column("new_items", sa.JSON(), nullable=False),
        sa.Column("operator_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sale_basket_id"], ["sale_baskets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_composition_histories_sale_basket_id"), "sale_composition_histories", ["sale_basket_id"], unique=False)

    op.create_table(
        "sale_reopen_histories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("operator_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_reopen_histories_sale_id"), "sale_reopen_histories", ["sale_id"], unique=False)

    op.create_table(
        "sale_delivery_histories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_basket_id", sa.Integer(), nullable=False),
        sa.Column("operator_name", sa.String(), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["sale_basket_id"], ["sale_baskets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_delivery_histories_sale_basket_id"), "sale_delivery_histories", ["sale_basket_id"], unique=False)


def downgrade() -> None:
    op.drop_table("sale_delivery_histories")
    op.drop_table("sale_reopen_histories")
    op.drop_table("sale_composition_histories")
    op.drop_table("sale_basket_items")
    op.drop_table("sale_baskets")
    op.drop_table("sales")
