"""add_payments_reservations_inspection

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-10-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create payments table
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        sa.CheckConstraint(
            "method IN ('PIX', 'CARTAO', 'DINHEIRO', 'OUTRO')",
            name="ck_payments_method",
        ),
        sa.UniqueConstraint("sale_id", "idempotency_key", name="uq_payments_sale_idempotency"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payments_sale_id"), "payments", ["sale_id"], unique=False)
    op.create_index(op.f("ix_payments_idempotency_key"), "payments", ["idempotency_key"], unique=False)

    # 2. Create sale_stock_reservations table
    op.create_table(
        "sale_stock_reservations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("current_quantity", sa.Numeric(), nullable=False),
        sa.Column("reserved_quantity", sa.Numeric(), nullable=False),
        sa.Column("consumed_quantity", sa.Numeric(), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("current_quantity >= 0", name="ck_reservations_current_quantity_non_negative"),
        sa.CheckConstraint("reserved_quantity >= 0", name="ck_reservations_reserved_quantity_non_negative"),
        sa.CheckConstraint("consumed_quantity >= 0", name="ck_reservations_consumed_quantity_non_negative"),
        sa.CheckConstraint("consumed_quantity <= reserved_quantity", name="ck_reservations_consumed_le_reserved"),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'RELEASED', 'CONSUMED')",
            name="ck_reservations_status",
        ),
        sa.UniqueConstraint("sale_id", "product_id", name="uq_reservations_sale_product"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_stock_reservations_sale_id"), "sale_stock_reservations", ["sale_id"], unique=False)
    op.create_index(op.f("ix_sale_stock_reservations_product_id"), "sale_stock_reservations", ["product_id"], unique=False)

    # 3. Create sale_cancellation_inspection table
    op.create_table(
        "sale_cancellation_inspection",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("consumed_quantity", sa.Numeric(), nullable=False),
        sa.Column("inspected_quantity", sa.Numeric(), server_default="0", nullable=False),
        sa.Column("reusable_quantity", sa.Numeric(), server_default="0", nullable=False),
        sa.Column("operator_name", sa.String(), nullable=False),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reintegrated_quantity", sa.Numeric(), server_default="0", nullable=False),
        sa.Column("reintegrated_movement_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.CheckConstraint("consumed_quantity > 0", name="ck_inspection_consumed_positive"),
        sa.CheckConstraint("inspected_quantity >= 0", name="ck_inspection_inspected_non_negative"),
        sa.CheckConstraint("inspected_quantity <= consumed_quantity", name="ck_inspection_inspected_le_consumed"),
        sa.CheckConstraint("reusable_quantity >= 0", name="ck_inspection_reusable_non_negative"),
        sa.CheckConstraint("reusable_quantity <= inspected_quantity", name="ck_inspection_reusable_le_inspected"),
        sa.CheckConstraint("reintegrated_quantity >= 0", name="ck_inspection_reintegrated_non_negative"),
        sa.CheckConstraint("reintegrated_quantity <= reusable_quantity", name="ck_inspection_reintegrated_le_reusable"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'INSPECTED', 'REINTEGRATED', 'DISCARDED')",
            name="ck_inspection_status",
        ),
        sa.UniqueConstraint("sale_id", "product_id", name="uq_inspection_sale_product"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reintegrated_movement_id"], ["inventory_movements.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_cancellation_inspection_sale_id"), "sale_cancellation_inspection", ["sale_id"], unique=False)

    # 4. Alter inventory_movements: add sale_id column
    op.add_column(
        "inventory_movements",
        sa.Column("sale_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_inventory_movements_sale_id",
        "inventory_movements",
        "sales",
        ["sale_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_inventory_movements_sale_id"), "inventory_movements", ["sale_id"], unique=False)

    # 5. Alter inventory_movements: update type check constraint to allow OUTPUT
    # Drop old constraint and create new one
    op.drop_constraint("ck_inventory_movements_type", "inventory_movements", type_="check")
    op.create_check_constraint(
        "ck_inventory_movements_type",
        "inventory_movements",
        "type IN ('ENTRY', 'ADJUSTMENT', 'OUTPUT')",
    )

    # 6. Alter inventory_movements: update quantity check constraint to allow negative for OUTPUT
    op.drop_constraint("ck_inventory_movements_quantity", "inventory_movements", type_="check")
    op.create_check_constraint(
        "ck_inventory_movements_quantity",
        "inventory_movements",
        "(type = 'ENTRY' AND quantity > 0) OR "
        "(type = 'ADJUSTMENT' AND quantity <> 0) OR "
        "(type = 'OUTPUT' AND quantity < 0)",
    )


def downgrade() -> None:
    # Reverse order of upgrade
    op.drop_constraint("ck_inventory_movements_quantity", "inventory_movements", type_="check")
    op.create_check_constraint(
        "ck_inventory_movements_quantity",
        "inventory_movements",
        "(type = 'ENTRY' AND quantity > 0) OR (type = 'ADJUSTMENT' AND quantity <> 0)",
    )

    op.drop_constraint("ck_inventory_movements_type", "inventory_movements", type_="check")
    op.create_check_constraint(
        "ck_inventory_movements_type",
        "inventory_movements",
        "type IN ('ENTRY', 'ADJUSTMENT')",
    )

    op.drop_index(op.f("ix_inventory_movements_sale_id"), table_name="inventory_movements")
    op.drop_constraint("fk_inventory_movements_sale_id", "inventory_movements", type_="foreignkey")
    op.drop_column("inventory_movements", "sale_id")

    op.drop_table("sale_cancellation_inspection")
    op.drop_table("sale_stock_reservations")
    op.drop_table("payments")
