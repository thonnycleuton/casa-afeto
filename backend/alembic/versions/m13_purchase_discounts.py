"""add_purchase_discounts

Revision ID: m13_purchase_discounts
Revises: m13_purchase_status_fiscal
Create Date: 2026-11-06 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm13_purchase_discounts'
down_revision: Union[str, None] = 'm13_purchase_status_fiscal'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add item_discounts JSONB column to purchase_items
    #    Use sa.JSON for SQLite compatibility; PostgreSQL will use JSONB via dialect.
    op.add_column(
        "purchase_items",
        sa.Column("item_discounts", sa.JSON, nullable=True),
    )

    # 2. Create purchase_document_discounts table
    op.create_table(
        "purchase_document_discounts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "purchase_id",
            sa.Integer,
            sa.ForeignKey("purchases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("value", sa.Numeric(10, 2, asdecimal=True), nullable=False),
        sa.Column("nature", sa.String(50), nullable=True),
        sa.Column("description", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("purchase_document_discounts")
    op.drop_column("purchase_items", "item_discounts")
