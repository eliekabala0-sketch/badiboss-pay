"""serdipay callback tracking

Revision ID: 3f1b5a7d9c20
Revises: 1d70f58dd134
Create Date: 2026-06-18 09:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '3f1b5a7d9c20'
down_revision = '1d70f58dd134'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('provider_session_id', sa.String(length=120), nullable=True))
    op.add_column('transactions', sa.Column('raw_payload', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('transactions', 'raw_payload')
    op.drop_column('transactions', 'provider_session_id')
