"""add_price_to_basket_templates

Revision ID: 60b1196c1918
Revises: 54c6b083a2df
Create Date: 2026-10-09 22:19:04.401183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60b1196c1918'
down_revision: Union[str, None] = '54c6b083a2df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "basket_templates",
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
    )
    op.create_check_constraint(
        "ck_basket_templates_price_non_negative",
        "basket_templates",
        "price >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_basket_templates_price_non_negative", "basket_templates", type_="check")
    op.drop_column("basket_templates", "price")
