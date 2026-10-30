"""add image_url to products

Revision ID: m10_add_product_image_url
Revises: m9_add_auth
Create Date: 2026-10-30
"""

from alembic import op
import sqlalchemy as sa

revision = "m10_add_product_image_url"
down_revision = "m9_add_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("image_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "image_url")
