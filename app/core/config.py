import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    app_name: str = "Badiboss Pay"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 120
    algorithm: str = "HS256"
    database_url: str = "sqlite:///./badiboss_pay.db"
    database_public_url: Optional[str] = None

    admin_email: str = "admin@badibosspay.com"
    admin_password: str = "admin12345"
    admin_force_password_reset: bool = False
    admin_full_name: str = "Badiboss Admin"

    serdipay_api_id: Optional[str] = None
    serdipay_api_password: Optional[str] = None
    serdipay_merchant_code: Optional[str] = None
    serdipay_pin: Optional[str] = None
    serdipay_outbound_proxy_url: Optional[str] = None
    serdipay_expected_outbound_ip: str = "66.33.22.87"
    serdipay_egress_check_url: str = "https://api.ipify.org?format=json"
    badiboss_public_domain: str = "pay.badiboss.com"

    client_callback_timeout_seconds: int = 8
    geoip_lookup_enabled: bool = True
    rate_limit_per_minute: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()


def _postgres_url_from_env() -> Optional[str]:
    host = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
    port = os.getenv("PGPORT") or os.getenv("POSTGRES_PORT")
    database = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB") or os.getenv("POSTGRES_DATABASE")
    username = os.getenv("PGUSER") or os.getenv("POSTGRES_USER")
    password = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD")

    if not all([host, database, username, password]):
        return None

    return URL.create(
        "postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=int(port) if port else None,
        database=database,
    ).render_as_string(hide_password=False)


def get_database_url() -> str:
    default_sqlite_url = "sqlite:///./badiboss_pay.db"
    if settings.database_public_url:
        return settings.database_public_url
    if settings.database_url != default_sqlite_url:
        return settings.database_url
    return _postgres_url_from_env() or settings.database_url
