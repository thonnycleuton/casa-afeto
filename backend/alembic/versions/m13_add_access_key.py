"""add access_key to purchases for OCR import deduplication

Revision ID: m13_add_access_key
Revises: m12_basket_template_image
Create Date: 2026-11-04 13:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm13_add_access_key'
down_revision: Union[str, None] = 'm12_basket_template_image'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add access_key column to purchases (nullable - manual purchases have no access key)
    op.add_column(
        "purchases",
        sa.Column("access_key", sa.String(length=44), nullable=True),
    )

    # Add UNIQUE constraint to prevent duplicate NF-e imports (D-8)
    op.create_unique_constraint(
        "uq_purchases_access_key",
        "purchases",
        ["access_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_purchases_access_key", "purchases", type_="unique")
    op.drop_column("purchases", "access_key")
