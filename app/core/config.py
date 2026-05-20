from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    admin_full_name: str = "Badiboss Admin"

    serdipay_api_id: Optional[str] = None
    serdipay_api_password: Optional[str] = None
    serdipay_merchant_code: Optional[str] = None
    serdipay_pin: Optional[str] = None

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


def get_database_url() -> str:
    return settings.database_public_url or settings.database_url
