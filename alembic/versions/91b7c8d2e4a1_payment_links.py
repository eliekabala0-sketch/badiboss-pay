"""payment links

Revision ID: 91b7c8d2e4a1
Revises: 8a2c4f91d6b7
Create Date: 2026-06-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "91b7c8d2e4a1"
down_revision = "8a2c4f91d6b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("success_redirect_url", sa.String(length=500), nullable=True),
        sa.Column("failure_redirect_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_links_id"), "payment_links", ["id"], unique=False)
    op.create_index(op.f("ix_payment_links_slug"), "payment_links", ["slug"], unique=True)
    op.add_column("transactions", sa.Column("payment_link_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "payment_link_id")
    op.drop_index(op.f("ix_payment_links_slug"), table_name="payment_links")
    op.drop_index(op.f("ix_payment_links_id"), table_name="payment_links")
    op.drop_table("payment_links")
