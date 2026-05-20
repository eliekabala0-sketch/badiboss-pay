import secrets


def generate_api_key() -> str:
    return f"bbp_api_{secrets.token_hex(16)}"


def generate_secret_key() -> str:
    return f"bbp_secret_{secrets.token_hex(24)}"
