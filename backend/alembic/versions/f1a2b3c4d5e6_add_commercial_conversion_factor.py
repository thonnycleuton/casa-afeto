"""Add commercial_conversion_factor to products.

Revision ID: f1a2b3c4d5e6
Revises: e5f6a7b8c9d0
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "commercial_conversion_factor",
            sa.Numeric(10, 2),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_products_commercial_conversion_factor_positive",
        "products",
        "commercial_conversion_factor IS NULL OR commercial_conversion_factor > 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_products_commercial_conversion_factor_positive", "products", type_="check"
    )
    op.drop_column("products", "commercial_conversion_factor")
