from __future__ import annotations


def normalize_drc_phone(value: str) -> str:
    """Return a DRC mobile number as 243 followed by nine local digits."""
    digits = "".join(character for character in str(value or "") if character.isdigit())
    if digits.startswith("243"):
        local = digits[3:]
    elif digits.startswith("0"):
        local = digits[1:]
    else:
        local = digits
    if len(local) != 9 or local.startswith("0"):
        raise ValueError("Le numero doit contenir 9 chiffres apres +243, sans zero initial")
    return f"243{local}"


def drc_local_phone(value: str) -> str:
    return normalize_drc_phone(value)[3:]
