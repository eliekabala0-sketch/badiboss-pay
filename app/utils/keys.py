import secrets
import re
import unicodedata


def generate_api_key() -> str:
    return f"bbpk_live_{secrets.token_urlsafe(24)}"


def generate_secret_key() -> str:
    return f"bbsk_live_{secrets.token_urlsafe(32)}"


def generate_webhook_secret() -> str:
    return f"bbwh_{secrets.token_urlsafe(32)}"


def generate_app_suffix() -> str:
    return secrets.token_hex(3)


def slugify_app_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or f"app-{generate_app_suffix()}"
