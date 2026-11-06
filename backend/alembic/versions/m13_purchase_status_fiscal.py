"""add_purchase_status_and_fiscal_data

Revision ID: m13_purchase_status_fiscal
Revises: m13_add_access_key
Create Date: 2026-11-05 23:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm13_purchase_status_fiscal'
down_revision: Union[str, None] = 'm13_add_access_key'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Status field with default CONFIRMED for existing records
    op.add_column(
        "purchases",
        sa.Column("status", sa.String(20), nullable=False, server_default="CONFIRMED"),
    )
    op.create_check_constraint(
        "ck_purchases_status",
        "purchases",
        "status IN ('DRAFT', 'CONFIRMED')",
    )

    # 2. Fiscal data fields (all optional)
    op.add_column(
        "purchases",
        sa.Column("supplier_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "purchases",
        sa.Column("cnpj", sa.String(20), nullable=True),
    )
    op.add_column(
        "purchases",
        sa.Column("invoice_number", sa.String(50), nullable=True),
    )
    op.add_column(
        "purchases",
        sa.Column("document_path", sa.String(500), nullable=True),
    )


def downgrade() -> None:
    op.drop_constraint("ck_purchases_status", "purchases", type_="check")
    op.drop_column("purchases", "document_path")
    op.drop_column("purchases", "invoice_number")
    op.drop_column("purchases", "cnpj")
    op.drop_column("purchases", "supplier_name")
    op.drop_column("purchases", "status")
