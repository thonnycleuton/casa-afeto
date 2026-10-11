"""Add reference_price to products.

Revision ID: a1b2c3d4e5f6
Revises: 8c39e24a71b1
Create Date: 2026-10-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8c39e24a71b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "reference_price",
            sa.Numeric(10, 2),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_products_reference_price_non_negative",
        "products",
        "reference_price IS NULL OR reference_price >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_products_reference_price_non_negative", "products", type_="check"
    )
    op.drop_column("products", "reference_price")
