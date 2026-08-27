from __future__ import annotations

import os
import hashlib
import socket
import uuid
from typing import Any
from urllib.parse import urlparse

import requests

from app.core.config import settings

DEFAULT_TOKEN_URL = "https://serdipay.com/api/public-api/v1/merchant/get-token"
DEFAULT_PAYMENT_URL = "https://serdipay.com/api/public-api/v1/merchant/payment-merchant"
TOKEN_URL = settings.serdipay_token_url or DEFAULT_TOKEN_URL
PAYMENT_URL = settings.serdipay_c2b_url or DEFAULT_PAYMENT_URL


def _serdipay_proxy_config() -> dict[str, str] | None:
    if not settings.serdipay_outbound_proxy_url:
        return None
    return {
        "http": settings.serdipay_outbound_proxy_url,
        "https": settings.serdipay_outbound_proxy_url,
    }


def _serdipay_request(method: str, url: str, **kwargs: Any) -> requests.Response:
    proxies = _serdipay_proxy_config()
    if proxies:
        kwargs["proxies"] = proxies
    return requests.request(method, url, **kwargs)


def _direct_request(method: str, url: str, **kwargs: Any) -> requests.Response:
    return requests.request(method, url, **kwargs)


def _observed_ip(proxies: dict[str, str] | None = None) -> dict:
    try:
        kwargs: dict[str, Any] = {"timeout": 15}
        if proxies:
            kwargs["proxies"] = proxies
        response = requests.get(settings.serdipay_egress_check_url, **kwargs)
        payload = response.json()
        observed_ip = payload.get("ip")
        return {
            "status_code": response.status_code,
            "observed_outbound_ip": observed_ip,
            "matches_expected_ip": observed_ip == settings.serdipay_expected_outbound_ip,
            "error": None,
        }
    except Exception as exc:
        return {
            "status_code": None,
            "observed_outbound_ip": None,
            "matches_expected_ip": False,
            "error": exc.__class__.__name__,
        }


def _public_domain_dns() -> dict:
    try:
        records = socket.getaddrinfo(settings.badiboss_public_domain, 443, type=socket.SOCK_STREAM)
        addresses = sorted({record[4][0] for record in records})
        return {"domain": settings.badiboss_public_domain, "addresses": addresses, "error": None}
    except Exception as exc:
        return {"domain": settings.badiboss_public_domain, "addresses": [], "error": exc.__class__.__name__}


def _proxy_summary(proxies: dict[str, str] | None) -> dict:
    if not proxies:
        return {"configured": False, "host": None, "port": None, "tcp_reachable": None}

    parsed = urlparse(proxies["https"])
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    reachable = False
    if host and port:
        try:
            with socket.create_connection((host, port), timeout=5):
                reachable = True
        except OSError:
            reachable = False
    return {"configured": True, "host": host, "port": port, "tcp_reachable": reachable}


TOKEN_KEYS = ("token", "access_token", "accessToken")
OFFICIAL_SERDIPAY_EMAIL = "eliekabala0@gmail.com"
MAIL_PASSWORD_SHA256_PREFIXES = {
    "mail_candidate_upper_I": "076559cf",
    "mail_candidate_lower_l": "374acb58",
}
SERDIPAY_VARIABLES = (
    "SERDIPAY_EMAIL",
    "SERDIPAY_PHONE",
    "SERDIPAY_PASSWORD",
    "SERDIPAY_MAIL_PASSWORD",
    "SERDIPAY_API_ID",
    "SERDIPAY_API_PASSWORD",
    "SERDIPAY_API_KEY",
    "SERDIPAY_MERCHANT_CODE",
    "SERDIPAY_PIN",
    "SERDIPAY_TOKEN_URL",
    "SERDIPAY_C2B_URL",
    "SERDIPAY_B2C_URL",
    "SERDIPAY_OUTBOUND_PROXY_URL",
    "SERDIPAY_EXPECTED_OUTBOUND_IP",
)
SECRET_KEYS = {
    "api_id",
    "apiId",
    "api_key",
    "apiKey",
    "api_password",
    "apiPassword",
    "password",
    "pin",
    "merchant_pin",
    "secret",
    "secret_key",
    "secretKey",
}
SECRET_KEY_FRAGMENTS = ("token", "password", "api_password", "pin", "authorization", "secret", "key")


def _setting_value(name: str) -> str | None:
    return getattr(settings, name.lower(), None)


def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "")}


def _masked_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    if len(text) <= 4:
        return "*" * len(text)
    return f"{text[:2]}***{text[-2:]}"


def _sha256_prefix(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:8]


def _detected_format(value: Any, name: str = "") -> str | None:
    if value in (None, ""):
        return None
    text = str(value)
    lower_name = name.lower()
    if text.startswith(("http://", "https://")):
        return "url"
    if "@" in text and "." in text:
        return "email_like"
    if text.isdigit() and 8 <= len(text) <= 15:
        return "phone_like"
    if text.isdigit():
        return "numeric"
    if any(word in lower_name for word in ("password", "pin", "key", "secret", "proxy")):
        return "secret_like"
    if len(text) >= 20:
        return "token_or_key_like"
    return "text"


def _variables_detected() -> dict[str, dict[str, Any]]:
    detected: dict[str, dict[str, Any]] = {}
    for name in SERDIPAY_VARIABLES:
        value = _setting_value(name)
        detected[name] = {
            "present": value not in (None, ""),
            "length": len(str(value)) if value not in (None, "") else 0,
            "format_detected": _detected_format(value, name),
            "masked_value": _masked_value(value),
            "source": "env" if os.getenv(name) else ("default" if value not in (None, "") else "missing"),
        }
    return detected


def _looks_like_email(value: str | None) -> bool:
    return bool(value and "@" in value and "." in value)


def _serdipay_token_email() -> str:
    if _looks_like_email(settings.serdipay_email):
        return str(settings.serdipay_email)
    return OFFICIAL_SERDIPAY_EMAIL


def _serdipay_token_password() -> str | None:
    if settings.serdipay_password:
        return settings.serdipay_password
    return settings.serdipay_api_password


def _official_token_payload() -> dict[str, Any]:
    return {
        "email": _serdipay_token_email(),
        "password": _serdipay_token_password(),
    }


def _password_matches_known_mail_candidate(value: Any) -> str | None:
    prefix = _sha256_prefix(value)
    for name, candidate_prefix in MAIL_PASSWORD_SHA256_PREFIXES.items():
        if prefix == candidate_prefix:
            return name
    return None


def _token_credentials_diagnostic(selected_password: Any, password_source: str) -> dict[str, Any]:
    raw_email = settings.serdipay_email
    return {
        "email_source": "SERDIPAY_EMAIL" if _looks_like_email(raw_email) else "official_fallback",
        "email_format_detected": _detected_format(_serdipay_token_email(), "SERDIPAY_EMAIL"),
        "password_source": password_source,
        "password_length": len(str(selected_password)) if selected_password else 0,
        "password_sha256_prefix": _sha256_prefix(selected_password),
        "password_format_detected": _detected_format(selected_password, "SERDIPAY_PASSWORD"),
        "api_password_length": len(str(settings.serdipay_api_password)) if settings.serdipay_api_password else 0,
        "api_password_sha256_prefix": _sha256_prefix(settings.serdipay_api_password),
        "api_password_format_detected": _detected_format(settings.serdipay_api_password, "SERDIPAY_API_PASSWORD"),
        "matches_mail_candidate": _password_matches_known_mail_candidate(selected_password),
        "mail_candidate_sha256_prefixes": MAIL_PASSWORD_SHA256_PREFIXES,
    }


def _token_payload_variants() -> list[dict[str, Any]]:
    variants = [
        {
            "name": "official_env_password_json",
            "password_source": "SERDIPAY_PASSWORD",
            "payload": {
                "email": _serdipay_token_email(),
                "password": settings.serdipay_password,
            },
        },
        {
            "name": "official_api_password_json",
            "password_source": "SERDIPAY_API_PASSWORD",
            "payload": {
                "email": _serdipay_token_email(),
                "password": settings.serdipay_api_password,
            },
        },
        {
            # This was the production token contract used by Badiboss Pay
            # before the email/password flow was introduced. Keep it as a
            # compatibility fallback: SerdiPay distinguishes dashboard users
            # (for example, Manager) from merchant API credentials.
            "name": "legacy_merchant_api_credentials_json",
            "password_source": "SERDIPAY_API_ID/SERDIPAY_API_PASSWORD/SERDIPAY_MERCHANT_CODE",
            "payload": {
                "api_id": settings.serdipay_api_id,
                "api_password": settings.serdipay_api_password,
                "merchantCode": settings.serdipay_merchant_code,
            },
        },
    ]
    if settings.serdipay_mail_password:
        variants.append(
            {
                "name": "official_mail_password_json",
                "password_source": "SERDIPAY_MAIL_PASSWORD",
                "payload": {
                    "email": _serdipay_token_email(),
                    "password": settings.serdipay_mail_password,
                },
            }
        )
    return [
        {**variant, "payload": _clean_payload(variant["payload"])}
        for variant in variants
        if variant["payload"].get("password") or variant["payload"].get("api_password")
    ]


def _send_token_request(payload: dict, proxies: dict[str, str] | None = None) -> requests.Response:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    kwargs: dict[str, Any] = {"headers": headers, "json": payload, "timeout": 20}
    if proxies:
        kwargs["proxies"] = proxies
    return requests.post(TOKEN_URL, **kwargs)


def _parse_response(response: requests.Response) -> dict:
    try:
        return response.json()
    except ValueError:
        return {"raw_response": response.text}


def _extract_token(payload: dict) -> str | None:
    for key in TOKEN_KEYS:
        value = payload.get(key)
        if value:
            return value
    for value in payload.values():
        if isinstance(value, dict):
            token = _extract_token(value)
            if token:
                return token
    return None


def _sanitize_response(payload: dict) -> dict:
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        if key in TOKEN_KEYS:
            sanitized[key] = "***TOKEN_MASKED***"
        elif key in SECRET_KEYS and not isinstance(value, (dict, list)):
            sanitized[key] = "***SECRET_MASKED***"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_response(value)
        elif isinstance(value, list):
            sanitized[key] = [_sanitize_response(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    return sanitized


def _is_sensitive_key(key: Any) -> bool:
    key_text = str(key)
    key_lower = key_text.lower()
    return key_text in SECRET_KEYS or any(fragment in key_lower for fragment in SECRET_KEY_FRAGMENTS)


def _known_secret_values(extra_secrets: tuple[Any, ...] = ()) -> list[str]:
    values = (
        settings.serdipay_api_password,
        settings.serdipay_password,
        settings.serdipay_mail_password,
        settings.serdipay_pin,
        settings.serdipay_api_key,
        settings.secret_key,
        settings.admin_password,
        *extra_secrets,
    )
    return sorted({str(value) for value in values if value not in (None, "")}, key=len, reverse=True)


def _mask_known_secrets(text: str, extra_secrets: tuple[Any, ...] = ()) -> str:
    masked = text
    for secret in _known_secret_values(extra_secrets):
        masked = masked.replace(secret, "***SECRET_MASKED***")
    return masked


def _sanitize_any(value: Any, extra_secrets: tuple[Any, ...] = ()) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if str(key) in TOKEN_KEYS:
                sanitized[key] = "***TOKEN_MASKED***"
            elif _is_sensitive_key(key):
                sanitized[key] = "***SECRET_MASKED***"
            else:
                sanitized[key] = _sanitize_any(item, extra_secrets=extra_secrets)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_any(item, extra_secrets=extra_secrets) for item in value]
    if isinstance(value, str):
        return _mask_known_secrets(value, extra_secrets=extra_secrets)
    return value


def _safe_error_message(exc: Exception, extra_secrets: tuple[Any, ...] = ()) -> str:
    return _mask_known_secrets(str(exc), extra_secrets=extra_secrets)


def _safe_token_test(proxies: dict[str, str] | None = None) -> dict:
    result = get_token(sanitize=True, include_attempts=False, proxies=proxies, use_configured_proxy=False)
    response = result.get("response", {})
    return {
        "endpoint": result.get("endpoint"),
        "status_code": result.get("status_code"),
        "variant": result.get("variant"),
        "content_type_used": result.get("content_type_used"),
        "payload_keys_sent": result.get("payload_keys_sent"),
        "token_present": result.get("token_present"),
        "response_keys": sorted(response.keys()) if isinstance(response, dict) else [],
        "message": response.get("message") if isinstance(response, dict) else None,
        "error": result.get("error"),
    }


def _response_errors(result: dict[str, Any]) -> dict[str, Any]:
    response = result.get("response")
    if isinstance(response, dict) and isinstance(response.get("errors"), dict):
        return response["errors"]
    return {}


def _token_failure_conclusion(attempts: list[dict[str, Any]]) -> str:
    if not attempts:
        return "Le test token officiel n'a pas pu etre execute."

    variable_map = _variables_detected()
    token_email = _serdipay_token_email()
    configured_password = _serdipay_token_password()
    if not _looks_like_email(token_email):
        return "SERDIPAY_EMAIL n'est pas une adresse email valide; l'endpoint officiel exige email/password en JSON."
    if not configured_password:
        return "SERDIPAY_PASSWORD ou SERDIPAY_API_PASSWORD est absent; l'endpoint officiel exige email/password en JSON."

    missing = [name for name, meta in variable_map.items() if name in ("SERDIPAY_PASSWORD", "SERDIPAY_API_PASSWORD", "SERDIPAY_MERCHANT_CODE", "SERDIPAY_PIN") and not meta["present"]]
    if missing:
        return f"Variables SerdiPay sensibles absentes ou vides: {', '.join(missing)}."

    last = attempts[-1]
    manager_role = any(
        "wrong user role" in str(attempt.get("response", {}).get("message", "")).lower()
        and "manager" in str(attempt.get("response", {}).get("message", "")).lower()
        for attempt in attempts
    )
    legacy_attempt = next((attempt for attempt in attempts if attempt.get("variant") == "legacy_merchant_api_credentials_json"), None)
    if manager_role and legacy_attempt and legacy_attempt.get("token_present"):
        return "Le login email/password est refuse comme Manager, mais les credentials API marchand historiques ont obtenu le token."
    if manager_role:
        return "SerdiPay reconnait le login email/password comme Manager. Le repli avec api_id/api_password/merchantCode a aussi ete tente; SerdiPay doit confirmer le contrat de token actif et le role API du marchand."
    if last.get("status_code") == 401:
        return "SerdiPay refuse les credentials fournis pour merchant/get-token."
    if last.get("status_code") == 400:
        return "SerdiPay retourne une validation 400 avec le payload officiel email/password JSON; verifier que SERDIPAY_EMAIL et SERDIPAY_PASSWORD correspondent exactement aux credentials API marchand."
    return "Le token n'est pas obtenu avec la methode officielle documentee; verifier les credentials API marchand fournis par SerdiPay."


def get_egress_diagnostic() -> dict:
    proxies = _serdipay_proxy_config()
    direct_egress = _observed_ip()
    proxy_egress = _observed_ip(proxies) if proxies else None
    public_dns = _public_domain_dns()
    proxy = _proxy_summary(proxies)

    if direct_egress["matches_expected_ip"]:
        conclusion = "Les appels directs sortent deja avec l'IP attendue par SerdiPay."
    elif proxy_egress and proxy_egress["matches_expected_ip"]:
        conclusion = "Les appels SerdiPay doivent passer par le proxy configure; ce proxy sort avec l'IP attendue."
    elif settings.serdipay_expected_outbound_ip in public_dns["addresses"]:
        conclusion = "L'IP attendue correspond au domaine public/edge Railway, mais pas a l'IP sortante du service. Elle ne peut pas etre utilisee comme egress sans passerelle controlee."
    elif not proxies:
        conclusion = "Aucun proxy SerdiPay n'est configure; les appels sortent avec l'egress Railway courant."
    else:
        conclusion = "Le proxy configure ne sort pas avec l'IP attendue ou n'est pas joignable."

    return {
        "public_domain": settings.badiboss_public_domain,
        "callback_url": f"https://{settings.badiboss_public_domain}/serdipay/callback",
        "public_domain_dns": public_dns,
        "proxy_configured": bool(proxies),
        "proxy": proxy,
        "expected_outbound_ip": settings.serdipay_expected_outbound_ip,
        "railway_direct_egress": direct_egress,
        "proxy_egress": proxy_egress,
        "serdipay_token_direct": _safe_token_test(),
        "serdipay_token_via_proxy": _safe_token_test(proxies) if proxies else None,
        "conclusion": conclusion,
    }


def get_token(
    sanitize: bool = False,
    include_attempts: bool = False,
    proxies: dict[str, str] | None = None,
    use_configured_proxy: bool = True,
) -> dict:
    attempts = []
    last_result: dict[str, Any] | None = None
    request_proxies = proxies if proxies is not None else (_serdipay_proxy_config() if use_configured_proxy else None)

    def attempt_summaries() -> list[dict[str, Any]]:
        return [{key: value for key, value in attempt.items() if key != "variables_detected"} for attempt in attempts]

    for variant in _token_payload_variants():
        payload = variant["payload"]
        selected_password = payload.get("password") or payload.get("api_password")
        password_source = variant["password_source"]
        try:
            response = _send_token_request(payload, proxies=request_proxies)
            data = _parse_response(response)
            token = _extract_token(data) if isinstance(data, dict) else None
            result = {
                "endpoint": TOKEN_URL,
                "variant": variant["name"],
                "password_source": password_source,
                "password_length": len(str(selected_password)) if selected_password else 0,
                "password_sha256_prefix": _sha256_prefix(selected_password),
                "matches_mail_candidate": _password_matches_known_mail_candidate(selected_password),
                "content_type_used": "application/json",
                "payload_keys_sent": sorted(payload.keys()),
                "status_code": response.status_code,
                "token_present": bool(token),
                "response": _sanitize_response(data) if sanitize and isinstance(data, dict) else data,
                "credential_diagnostic": _token_credentials_diagnostic(selected_password, password_source),
                "error": None,
            }
        except Exception as exc:
            result = {
                "endpoint": TOKEN_URL,
                "variant": variant["name"],
                "password_source": password_source,
                "password_length": len(str(selected_password)) if selected_password else 0,
                "password_sha256_prefix": _sha256_prefix(selected_password),
                "matches_mail_candidate": _password_matches_known_mail_candidate(selected_password),
                "content_type_used": "application/json",
                "payload_keys_sent": sorted(payload.keys()),
                "status_code": None,
                "token_present": False,
                "response": {},
                "credential_diagnostic": _token_credentials_diagnostic(selected_password, password_source),
                "error": exc.__class__.__name__,
            }

        attempts.append(result)
        last_result = result
        if result["token_present"]:
            if include_attempts:
                result["attempts"] = attempt_summaries()
            return result

    if last_result is None:
        last_result = {"endpoint": TOKEN_URL, "status_code": None, "response": {}, "token_present": False, "error": "NoTokenVariants"}
    # A fallback payload can fail validation after the primary email/password
    # request has already produced the actionable provider error. Preserve the
    # latter for payment callers and customer-facing failure messages.
    role_failure = next(
        (
            attempt
            for attempt in attempts
            if "wrong user role" in str(attempt.get("response", {}).get("message", "")).lower()
        ),
        None,
    )
    if role_failure:
        last_result = role_failure
    if include_attempts:
        last_result["attempts"] = attempt_summaries()
        last_result["conclusion_probable"] = _token_failure_conclusion(attempts)
    return last_result


def _normalize_client_phone(phone: str) -> str:
    normalized = "".join(character for character in str(phone or "") if character.isdigit())
    if normalized.startswith("0"):
        normalized = f"243{normalized[1:]}"
    return normalized


def _normalize_telecom(telecom: str) -> str:
    value = str(telecom or "OM").strip().upper()
    aliases = {"AFRIMONEY": "AF", "ORANGE": "OM", "AIRTEL": "AM", "MPESA": "MP", "M-PESA": "MP"}
    return aliases.get(value, value)


def create_payment(phone: str, amount: float, currency: str, telecom: str = "OM") -> dict:
    token_data = get_token()
    token_response = token_data.get("response", {})
    access_token = _extract_token(token_response) if isinstance(token_response, dict) else None
    reference = str(uuid.uuid4())
    sanitized_token_data = {**token_data, "response": _sanitize_response(token_response)} if isinstance(token_response, dict) else token_data
    if not access_token:
        token_error = _sanitize_any(token_response) if isinstance(token_response, dict) else {}
        message = token_error.get("message") or token_error.get("error") or "SerdiPay token unavailable"
        return {
            "reference": reference,
            "token_response": sanitized_token_data,
            "payment_payload_keys_sent": [],
            "serdipay_status_code": token_data.get("status_code") or 401,
            "serdipay_response": {"message": f"SerdiPay token unavailable: {message}"},
        }

    payload = {
        "api_id": settings.serdipay_api_id,
        "api_password": settings.serdipay_api_password,
        "merchantCode": settings.serdipay_merchant_code,
        "merchant_pin": settings.serdipay_pin,
        "clientPhone": _normalize_client_phone(phone),
        "amount": amount,
        "currency": currency,
        "telecom": _normalize_telecom(telecom),
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": f"Bearer {access_token}"}
    try:
        response = _serdipay_request("POST", PAYMENT_URL, json=payload, headers=headers, timeout=25)
    except requests.RequestException as exc:
        return {
            "reference": reference,
            "token_response": sanitized_token_data,
            "payment_payload_keys_sent": sorted(payload.keys()),
            "serdipay_status_code": 503,
            "serdipay_response": {"message": f"SerdiPay payment request failed: {_safe_error_message(exc, extra_secrets=(access_token,))}"},
        }
    try:
        response_payload = response.json()
    except ValueError:
        response_payload = {"raw_response": response.text}

    return {
        "reference": reference,
        "token_response": sanitized_token_data,
        "payment_payload_keys_sent": sorted(payload.keys()),
        "serdipay_status_code": response.status_code,
        "serdipay_response": _sanitize_any(response_payload, extra_secrets=(access_token,)),
    }


def create_test_payment_diagnostic(
    phone: str | None,
    amount: float | None = None,
    currency: str | None = None,
    telecom: str = "OM",
) -> dict:
    diagnostic = {
        "step": "token_request",
        "token_obtained": False,
        "serdipay_endpoint": PAYMENT_URL,
        "payload_keys_sent": [],
        "authorization_header_present": False,
        "status_code_serdipay": None,
        "response_serdipay": None,
        "error_type": None,
        "error_message": None,
    }

    access_token = None
    try:
        token_data = get_token(sanitize=False)
        token_response = token_data.get("response", {})
        access_token = _extract_token(token_response) if isinstance(token_response, dict) else None
        diagnostic["token_obtained"] = bool(access_token)
        if not access_token:
            diagnostic.update(
                {
                    "step": "token_response",
                    "status_code_serdipay": token_data.get("status_code"),
                    "response_serdipay": _sanitize_any(token_response),
                    "error_type": token_data.get("error") or "TokenUnavailable",
                    "error_message": "SerdiPay token unavailable",
                }
            )
            return diagnostic
    except Exception as exc:
        diagnostic.update(
            {
                "step": "token_request",
                "error_type": exc.__class__.__name__,
                "error_message": _safe_error_message(exc),
            }
        )
        return diagnostic

    payment_amount = amount if amount is not None else 100
    payload = {
        "api_id": settings.serdipay_api_id,
        "api_password": settings.serdipay_api_password,
        "merchantCode": settings.serdipay_merchant_code,
        "merchant_pin": settings.serdipay_pin,
        "clientPhone": _normalize_client_phone(phone or settings.serdipay_phone or ""),
        "amount": payment_amount,
        "currency": str(currency).upper() if currency else None,
        "telecom": _normalize_telecom(telecom),
    }
    diagnostic["payload_keys_sent"] = sorted(payload.keys())

    if not payload["clientPhone"]:
        diagnostic.update(
            {
                "step": "payload_validation",
                "authorization_header_present": True,
                "error_type": "MissingClientPhone",
                "error_message": "clientPhone is required for the SerdiPay test payload.",
            }
        )
        return diagnostic
    if not currency:
        diagnostic.update(
            {
                "step": "payload_validation",
                "authorization_header_present": True,
                "error_type": "MissingCurrency",
                "error_message": "currency is required for the SerdiPay test payload.",
            }
        )
        return diagnostic

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    diagnostic["authorization_header_present"] = bool(headers.get("Authorization"))

    try:
        diagnostic["step"] = "serdipay_payment_request"
        response = _serdipay_request("POST", PAYMENT_URL, json=payload, headers=headers, timeout=25)
        diagnostic["status_code_serdipay"] = response.status_code
        diagnostic["response_serdipay"] = _sanitize_any(_parse_response(response), extra_secrets=(access_token,))
        if response.status_code >= 400:
            diagnostic["error_type"] = "SerdiPayHTTPError"
            diagnostic["error_message"] = f"SerdiPay returned HTTP {response.status_code}"
    except Exception as exc:
        diagnostic.update(
            {
                "step": "serdipay_payment_request",
                "error_type": exc.__class__.__name__,
                "error_message": _safe_error_message(exc, extra_secrets=(access_token,)),
            }
        )

    return diagnostic
