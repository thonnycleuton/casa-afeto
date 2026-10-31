"""add image_url to basket_templates

Revision ID: m12_basket_template_image
Revises: m11_add_customer_image_url
Create Date: 2026-10-30
"""

from alembic import op
import sqlalchemy as sa

revision = "m12_basket_template_image"
down_revision = "m11_add_customer_image_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("basket_templates", sa.Column("image_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("basket_templates", "image_url")
