"""add stock batches

Revision ID: m7_add_stock_batches
Revises: d1e2f3a4b5c6
Create Date: 2026-10-19 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm7_add_stock_batches'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create stock_batches table
    op.create_table(
        "stock_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("purchase_id", sa.Integer(), nullable=True),
        sa.Column("purchase_item_id", sa.Integer(), nullable=True),
        sa.Column("quantity_original", sa.Numeric(), nullable=False),
        sa.Column("quantity_remaining", sa.Numeric(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity_original > 0", name="ck_stock_batches_quantity_original_positive"),
        sa.CheckConstraint("quantity_remaining >= 0", name="ck_stock_batches_quantity_remaining_non_negative"),
        sa.CheckConstraint("unit_cost IS NULL OR unit_cost >= 0", name="ck_stock_batches_unit_cost_non_negative"),
        sa.CheckConstraint("status IN ('ACTIVE', 'EXHAUSTED')", name="ck_stock_batches_status"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_stock_batches_product_id"), "stock_batches", ["product_id"], unique=False)
    op.create_index(op.f("ix_stock_batches_purchase_id"), "stock_batches", ["purchase_id"], unique=False)

    # 2. Add batch_id to inventory_movements
    op.add_column(
        "inventory_movements",
        sa.Column("batch_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_inventory_movements_batch_id",
        "inventory_movements",
        "stock_batches",
        ["batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_inventory_movements_batch_id"), "inventory_movements", ["batch_id"], unique=False)

    # 3. Migrate existing ENTRY movements to stock batches
    conn = op.get_bind()
    # Select all ENTRY movements grouped by product_id, purchase_id, unit_cost, created_at
    rows = conn.execute(
        sa.text("""
            SELECT id, product_id, quantity, unit_cost, purchase_id, created_at
            FROM inventory_movements
            WHERE type = 'ENTRY'
            ORDER BY created_at, id
        """)
    ).fetchall()
    for row in rows:
        movement_id, product_id, quantity, unit_cost, purchase_id, created_at = row
        conn.execute(
            sa.text("""
                INSERT INTO stock_batches
                    (product_id, purchase_id, quantity_original, quantity_remaining, unit_cost, status, created_at)
                VALUES (:product_id, :purchase_id, :quantity, :quantity, :unit_cost, 'ACTIVE', :created_at)
            """),
            {
                "product_id": product_id,
                "purchase_id": purchase_id,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "created_at": created_at,
            },
        )
        # Get the inserted batch id
        result = conn.execute(
            sa.text("""
                SELECT id FROM stock_batches
                WHERE product_id = :product_id AND purchase_id = :purchase_id_or_null
                  AND quantity_original = :quantity AND created_at = :created_at
                ORDER BY id DESC LIMIT 1
            """),
            {
                "product_id": product_id,
                "purchase_id_or_null": purchase_id if purchase_id is not None else -1,
                "quantity": quantity,
                "created_at": created_at,
            },
        )
        batch_id = result.scalar()
        if batch_id is not None:
            conn.execute(
                sa.text("""
                    UPDATE inventory_movements SET batch_id = :batch_id WHERE id = :movement_id
                """),
                {"batch_id": batch_id, "movement_id": movement_id},
            )


def downgrade() -> None:
    op.drop_index(op.f("ix_inventory_movements_batch_id"), table_name="inventory_movements")
    op.drop_constraint("fk_inventory_movements_batch_id", "inventory_movements", type_="foreignkey")
    op.drop_column("inventory_movements", "batch_id")

    op.drop_table("stock_batches")
