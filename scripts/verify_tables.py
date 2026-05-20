from sqlalchemy import create_engine, inspect, text

from app.core.config import get_database_url


def main() -> None:
    engine = create_engine(get_database_url())
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    print("TABLE_COUNT", len(tables))
    for table in tables:
        print(table)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT table_name "
                "FROM information_schema.tables "
                "WHERE table_schema = 'public' "
                "ORDER BY table_name"
            )
        ).fetchall()
    print("PUBLIC_TABLES", len(rows))
    for row in rows:
        print(row[0])


if __name__ == "__main__":
    main()
