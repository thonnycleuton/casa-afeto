"""add expiry date to stock batches and purchase items

Revision ID: m8_add_expiry
Revises: m7_add_stock_batches
Create Date: 2026-10-20 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm8_add_expiry'
down_revision: Union[str, None] = 'm7_add_stock_batches'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add expiry_date to stock_batches (nullable - existing batches have no expiry)
    op.add_column(
        "stock_batches",
        sa.Column("expiry_date", sa.Date(), nullable=True),
    )

    # 2. Add expiry_date to purchase_items (nullable - existing items have no expiry)
    op.add_column(
        "purchase_items",
        sa.Column("expiry_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("purchase_items", "expiry_date")
    op.drop_column("stock_batches", "expiry_date")
