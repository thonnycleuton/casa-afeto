"""add_unit_cost_to_inventory_movements

Revision ID: 65e00c126251
Revises: 60b1196c1918
Create Date: 2026-10-10 00:07:47.672229

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65e00c126251'
down_revision: Union[str, None] = '60b1196c1918'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "inventory_movements",
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=True),
    )
    op.create_check_constraint(
        "ck_inventory_movements_unit_cost_non_negative",
        "inventory_movements",
        "unit_cost IS NULL OR unit_cost >= 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_inventory_movements_unit_cost_non_negative",
        "inventory_movements",
        type_="check",
    )
    op.drop_column("inventory_movements", "unit_cost")
