from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def ensure_runtime_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "transactions" not in table_names:
        return

    transaction_columns = {column["name"] for column in inspector.get_columns("transactions")}
    statements = []
    if "provider_session_id" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN provider_session_id VARCHAR(120)")
    if "raw_payload" not in transaction_columns:
        statements.append("ALTER TABLE transactions ADD COLUMN raw_payload TEXT")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
