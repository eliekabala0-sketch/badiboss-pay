from alembic import command
from alembic.config import Config

from app.core.config import database_backend, get_database_url


def run_alembic_upgrade_if_persistent() -> bool:
    if database_backend() != "postgresql":
        return False
    config = Config("alembic.ini")
    config.attributes["database_url"] = get_database_url()
    command.upgrade(config, "head")
    return True
