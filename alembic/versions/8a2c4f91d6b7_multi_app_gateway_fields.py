"""multi app gateway fields

Revision ID: 8a2c4f91d6b7
Revises: 3f1b5a7d9c20
Create Date: 2026-06-27 00:00:00.000000

"""
import re
import secrets
import unicodedata

from alembic import op
import sqlalchemy as sa


revision = "8a2c4f91d6b7"
down_revision = "3f1b5a7d9c20"
branch_labels = None
depends_on = None


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or f"app-{secrets.token_hex(3)}"


def upgrade() -> None:
    op.add_column("connected_apps", sa.Column("app_slug", sa.String(length=120), nullable=True))
    op.add_column("connected_apps", sa.Column("webhook_secret", sa.String(length=128), nullable=True))
    op.add_column("transactions", sa.Column("customer_name", sa.String(length=255), nullable=True))
    op.add_column("transactions", sa.Column("callback_url", sa.String(length=500), nullable=True))
    op.add_column("transactions", sa.Column("metadata_json", sa.Text(), nullable=True))
    op.add_column(
        "transactions",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, name, app_id FROM connected_apps ORDER BY id")).mappings().all()
    used_slugs: set[str] = set()
    for row in rows:
        base_slug = _slugify(row["name"] or row["app_id"])
        slug = base_slug
        counter = 2
        while slug in used_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        used_slugs.add(slug)
        connection.execute(
            sa.text(
                """
                UPDATE connected_apps
                SET app_slug = :app_slug,
                    webhook_secret = COALESCE(webhook_secret, :webhook_secret)
                WHERE id = :id
                """
            ),
            {"app_slug": slug, "webhook_secret": f"bbwh_{secrets.token_urlsafe(32)}", "id": row["id"]},
    )

    op.create_index(op.f("ix_connected_apps_app_slug"), "connected_apps", ["app_slug"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_connected_apps_app_slug"), table_name="connected_apps")
    op.drop_column("transactions", "updated_at")
    op.drop_column("transactions", "metadata_json")
    op.drop_column("transactions", "callback_url")
    op.drop_column("transactions", "customer_name")
    op.drop_column("connected_apps", "webhook_secret")
    op.drop_column("connected_apps", "app_slug")
