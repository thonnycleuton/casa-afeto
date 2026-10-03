"""Create M1 products and inventory tables.

Revision ID: 91a4d2c80f31
Revises: b615096c30ba
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91a4d2c80f31"
down_revision: Union[str, None] = "b615096c30ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("base_unit", sa.String(length=2), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "base_unit IN ('UN', 'KG', 'G', 'L', 'ML')",
            name="ck_products_base_unit",
        ),
    )
    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "type IN ('ENTRY', 'ADJUSTMENT')",
            name="ck_inventory_movements_type",
        ),
        sa.CheckConstraint(
            "(type = 'ENTRY' AND quantity > 0) OR "
            "(type = 'ADJUSTMENT' AND quantity <> 0)",
            name="ck_inventory_movements_quantity",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_inventory_movements_product_id_products",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_inventory_movements_product_id",
        "inventory_movements",
        ["product_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_inventory_movements_product_id", table_name="inventory_movements"
    )
    op.drop_table("inventory_movements")
    op.drop_table("products")
