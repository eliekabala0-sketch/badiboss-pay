import re
import secrets
import unicodedata

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or f"app-{secrets.token_hex(3)}"


def ensure_runtime_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "transactions" not in table_names:
        return

    transaction_columns = {column["name"] for column in inspector.get_columns("transactions")}
    app_columns = {column["name"] for column in inspector.get_columns("connected_apps")} if "connected_apps" in table_names else set()
    statements = []
    if "payment_links" not in table_names:
        statements.append(
            """
            CREATE TABLE payment_links (
                id INTEGER PRIMARY KEY,
                slug VARCHAR(160) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                amount FLOAT NOT NULL,
                currency VARCHAR(10) NOT NULL,
                expires_at TIMESTAMP,
                max_uses INTEGER,
                success_redirect_url VARCHAR(500),
                failure_redirect_url VARCHAR(500),
                status VARCHAR(30) NOT NULL,
                is_active BOOLEAN NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )
    if "app_slug" not in app_columns:
        statements.append("ALTER TABLE connected_apps ADD COLUMN app_slug VARCHAR(120)")
    if "webhook_secret" not in app_columns:
        statements.append("ALTER TABLE connected_apps ADD COLUMN webhook_secret VARCHAR(128)")
    if "customer_name" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN customer_name VARCHAR(255)")
    if "payment_link_id" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN payment_link_id INTEGER")
    if "provider_session_id" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN provider_session_id VARCHAR(120)")
    if "raw_payload" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN raw_payload TEXT")
    if "callback_url" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN callback_url VARCHAR(500)")
    if "metadata_json" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN metadata_json TEXT")
    if "updated_at" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN updated_at TIMESTAMP")

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        if "connected_apps" in table_names:
            rows = connection.execute(text("SELECT id, name, app_id, app_slug, webhook_secret FROM connected_apps ORDER BY id")).mappings().all()
            used_slugs: set[str] = {str(row["app_slug"]) for row in rows if row["app_slug"]}
            for row in rows:
                slug = row["app_slug"]
                if not slug:
                    base_slug = _slugify(row["name"] or row["app_id"])
                    slug = base_slug
                    counter = 2
                    while slug in used_slugs:
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    used_slugs.add(slug)
                webhook_secret = row["webhook_secret"] or f"bbwh_{secrets.token_urlsafe(32)}"
                connection.execute(
                    text(
                        """
                        UPDATE connected_apps
                        SET app_slug = :app_slug,
                            webhook_secret = :webhook_secret
                        WHERE id = :id
                        """
                    ),
                    {"app_slug": slug, "webhook_secret": webhook_secret, "id": row["id"]},
                )
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_connected_apps_app_slug ON connected_apps (app_slug)"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_payment_links_slug ON payment_links (slug)"))
        connection.execute(
            text(
                """
                UPDATE transactions
                SET updated_at = created_at
                WHERE updated_at IS NULL
                """
            )
        )
        connection.execute(
            text(
                """
                UPDATE transactions
                SET currency = 'UNKNOWN',
                    payment_method = 'callback_test',
                    source_application = 'SerdiPay callback test'
                WHERE provider = 'serdipay'
                  AND app_id = 'serdipay'
                  AND amount = 0
                  AND currency = 'CDF'
                  AND raw_payload IS NOT NULL
                  AND raw_payload NOT LIKE '%"amount"%'
                  AND raw_payload NOT LIKE '%"currency"%'
                """
            )
        )
