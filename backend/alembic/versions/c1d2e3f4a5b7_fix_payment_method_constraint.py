"""fix payment method constraint to PIX and CARTAO only

Revision ID: c1d2e3f4a5b7
Revises: c1d2e3f4a5b6
Create Date: 2026-10-12 17:45:00.000000

The previous migration (c1d2e3f4a5b6) created ck_payments_method accepting
'PIX', 'CARTAO', 'DINHEIRO', 'OUTRO'. Business decision approved only PIX
and CARTAO. This migration replaces the constraint to reject DINHEIRO and
OUTRO.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b7'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_payments_method", "payments", type_="check")
    op.create_check_constraint(
        "ck_payments_method",
        "payments",
        "method IN ('PIX', 'CARTAO')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_payments_method", "payments", type_="check")
    op.create_check_constraint(
        "ck_payments_method",
        "payments",
        "method IN ('PIX', 'CARTAO', 'DINHEIRO', 'OUTRO')",
    )
