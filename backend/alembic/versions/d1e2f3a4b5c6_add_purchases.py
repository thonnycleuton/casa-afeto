"""add_purchases

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b7
Create Date: 2026-10-15 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c1d2e3f4a5b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create purchases table
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchased_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_purchases_purchased_at"), "purchases", ["purchased_at"], unique=False)

    # 2. Create purchase_items table
    op.create_table(
        "purchase_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("commercial_unit", sa.String(length=50), nullable=True),
        sa.Column("conversion_factor", sa.Numeric(), nullable=False),
        sa.Column("commercial_quantity", sa.Numeric(), nullable=False),
        sa.Column("commercial_unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("conversion_factor > 0", name="ck_purchase_items_conversion_factor_positive"),
        sa.CheckConstraint("commercial_quantity > 0", name="ck_purchase_items_quantity_positive"),
        sa.CheckConstraint("commercial_unit_price >= 0", name="ck_purchase_items_price_non_negative"),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_purchase_items_purchase_id"), "purchase_items", ["purchase_id"], unique=False)
    op.create_index(op.f("ix_purchase_items_product_id"), "purchase_items", ["product_id"], unique=False)

    # 3. Add purchase_id to inventory_movements
    op.add_column(
        "inventory_movements",
        sa.Column("purchase_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_inventory_movements_purchase_id",
        "inventory_movements",
        "purchases",
        ["purchase_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_inventory_movements_purchase_id"), "inventory_movements", ["purchase_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_inventory_movements_purchase_id"), table_name="inventory_movements")
    op.drop_constraint("fk_inventory_movements_purchase_id", "inventory_movements", type_="foreignkey")
    op.drop_column("inventory_movements", "purchase_id")

    op.drop_table("purchase_items")
    op.drop_table("purchases")
