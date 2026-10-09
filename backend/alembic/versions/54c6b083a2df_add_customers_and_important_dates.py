"""Add customers and important dates for M3.

Revision ID: 54c6b083a2df
Revises: 7c30bd49a21f
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "54c6b083a2df"
down_revision: Union[str, None] = "7c30bd49a21f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="ACTIVE"),
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
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_customers_status"),
    )
    op.create_table(
        "important_dates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("recurring", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("day", sa.Integer(), nullable=True),
        sa.Column("month", sa.Integer(), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="ACTIVE"),
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
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="ck_important_dates_status",
        ),
        sa.CheckConstraint(
            "((recurring = true AND day IS NOT NULL AND month IS NOT NULL AND day BETWEEN 1 AND 31 AND month BETWEEN 1 AND 12 AND date IS NULL) OR (recurring = false AND date IS NOT NULL AND day IS NULL AND month IS NULL))",
            name="ck_important_dates_value",
        ),
    )
    op.create_index("ix_important_dates_customer_id", "important_dates", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_important_dates_customer_id", table_name="important_dates")
    op.drop_table("important_dates")
    op.drop_table("customers")
