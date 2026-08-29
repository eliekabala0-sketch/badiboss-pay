"""add withdrawal destinations and payout audit fields

Revision ID: d7e4f9a2b1c6
Revises: c4a8d1e7f29b
Create Date: 2026-08-29 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "d7e4f9a2b1c6"
down_revision = "c4a8d1e7f29b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("withdrawals", sa.Column("destination_type", sa.String(length=30), nullable=True))
    op.add_column("withdrawals", sa.Column("mobile_operator", sa.String(length=30), nullable=True))
    op.add_column("withdrawals", sa.Column("mobile_phone", sa.String(length=30), nullable=True))
    op.add_column("withdrawals", sa.Column("bank_name", sa.String(length=160), nullable=True))
    op.add_column("withdrawals", sa.Column("account_name", sa.String(length=160), nullable=True))
    op.add_column("withdrawals", sa.Column("account_number", sa.String(length=120), nullable=True))
    op.add_column("withdrawals", sa.Column("bank_swift", sa.String(length=40), nullable=True))
    op.add_column("withdrawals", sa.Column("provider_reference", sa.String(length=160), nullable=True))
    op.add_column("withdrawals", sa.Column("failure_reason", sa.String(length=500), nullable=True))
    op.add_column("withdrawals", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("settlements", sa.Column("withdrawal_reference", sa.String(length=80), nullable=True))
    op.add_column("settlements", sa.Column("destination_type", sa.String(length=30), nullable=True))
    op.add_column("settlements", sa.Column("provider_reference", sa.String(length=160), nullable=True))
    op.create_index("ix_settlements_withdrawal_reference", "settlements", ["withdrawal_reference"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_settlements_withdrawal_reference", table_name="settlements")
    op.drop_column("settlements", "provider_reference")
    op.drop_column("settlements", "destination_type")
    op.drop_column("settlements", "withdrawal_reference")
    op.drop_column("withdrawals", "processed_at")
    op.drop_column("withdrawals", "failure_reason")
    op.drop_column("withdrawals", "provider_reference")
    op.drop_column("withdrawals", "bank_swift")
    op.drop_column("withdrawals", "account_number")
    op.drop_column("withdrawals", "account_name")
    op.drop_column("withdrawals", "bank_name")
    op.drop_column("withdrawals", "mobile_phone")
    op.drop_column("withdrawals", "mobile_operator")
    op.drop_column("withdrawals", "destination_type")
