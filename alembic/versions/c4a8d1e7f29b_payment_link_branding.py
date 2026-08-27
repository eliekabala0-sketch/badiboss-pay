"""add payment-link branding

Revision ID: c4a8d1e7f29b
Revises: 91b7c8d2e4a1
Create Date: 2026-08-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "c4a8d1e7f29b"
down_revision = "91b7c8d2e4a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payment_links", sa.Column("brand_name", sa.String(length=120), nullable=True))
    op.add_column("payment_links", sa.Column("brand_logo_url", sa.String(length=500), nullable=True))
    op.add_column("payment_links", sa.Column("custom_domain", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("payment_links", "custom_domain")
    op.drop_column("payment_links", "brand_logo_url")
    op.drop_column("payment_links", "brand_name")
