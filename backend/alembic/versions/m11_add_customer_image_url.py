"""add image_url to customers

Revision ID: m11_add_customer_image_url
Revises: m10_add_product_image_url
Create Date: 2026-10-30
"""

from alembic import op
import sqlalchemy as sa

revision = "m11_add_customer_image_url"
down_revision = "m10_add_product_image_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("image_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("customers", "image_url")
