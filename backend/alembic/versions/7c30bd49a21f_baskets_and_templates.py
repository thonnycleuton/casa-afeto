"""Add baskets and basket templates for M2.

Revision ID: 7c30bd49a21f
Revises: 91a4d2c80f31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c30bd49a21f"
down_revision: Union[str, None] = "91a4d2c80f31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "basket_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "basket_template_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id"], ["basket_templates.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("template_id", "product_id", name="uq_basket_template_items_product"),
        sa.CheckConstraint("quantity > 0", name="ck_basket_template_items_quantity_positive"),
    )
    op.create_index(
        "ix_basket_template_items_product_id",
        "basket_template_items",
        ["product_id"],
    )
    op.create_table(
        "baskets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["template_id"], ["basket_templates.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_baskets_template_id", "baskets", ["template_id"])
    op.create_table(
        "basket_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("basket_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.ForeignKeyConstraint(["basket_id"], ["baskets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("basket_id", "product_id", name="uq_basket_items_product"),
        sa.CheckConstraint("quantity > 0", name="ck_basket_items_quantity_positive"),
    )
    op.create_index("ix_basket_items_product_id", "basket_items", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_basket_items_product_id", table_name="basket_items")
    op.drop_table("basket_items")
    op.drop_index("ix_baskets_template_id", table_name="baskets")
    op.drop_table("baskets")
    op.drop_index("ix_basket_template_items_product_id", table_name="basket_template_items")
    op.drop_table("basket_template_items")
    op.drop_table("basket_templates")
