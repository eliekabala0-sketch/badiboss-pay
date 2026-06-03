import os
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
SERDIPAY_VARIABLES = (
    "SERDIPAY_EMAIL",
    "SERDIPAY_PHONE",
    "SERDIPAY_PASSWORD",
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


def _token_payload_variants() -> list[dict[str, Any]]:
    return [{"name": "official_email_password_json", "payload": _clean_payload(_official_token_payload())}]


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
    if last.get("status_code") == 401:
        return "Le format officiel email/password JSON est correct, mais SerdiPay refuse les credentials fournis pour merchant/get-token."
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
        try:
            response = _send_token_request(payload, proxies=request_proxies)
            data = _parse_response(response)
            token = _extract_token(data) if isinstance(data, dict) else None
            result = {
                "endpoint": TOKEN_URL,
                "variant": variant["name"],
                "content_type_used": "application/json",
                "payload_keys_sent": sorted(payload.keys()),
                "status_code": response.status_code,
                "token_present": bool(token),
                "response": _sanitize_response(data) if sanitize and isinstance(data, dict) else data,
                "error": None,
            }
        except Exception as exc:
            result = {
                "endpoint": TOKEN_URL,
                "variant": variant["name"],
                "content_type_used": "application/json",
                "payload_keys_sent": sorted(payload.keys()),
                "status_code": None,
                "token_present": False,
                "response": {},
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
    if include_attempts:
        last_result["attempts"] = attempt_summaries()
        last_result["conclusion_probable"] = _token_failure_conclusion(attempts)
    return last_result


def create_payment(phone: str, amount: float, currency: str = "CDF", telecom: str = "AM") -> dict:
    token_data = get_token()
    token_response = token_data.get("response", {})
    access_token = _extract_token(token_response) if isinstance(token_response, dict) else None
    reference = str(uuid.uuid4())
    sanitized_token_data = {**token_data, "response": _sanitize_response(token_response)} if isinstance(token_response, dict) else token_data
    if not access_token:
        return {
            "reference": reference,
            "token_response": sanitized_token_data,
            "payment_payload_keys_sent": [],
            "serdipay_status_code": token_data.get("status_code") or 401,
            "serdipay_response": {"message": "SerdiPay token unavailable"},
        }

    payload = {
        "api_id": settings.serdipay_api_id,
        "api_password": settings.serdipay_api_password,
        "merchantCode": settings.serdipay_merchant_code,
        "merchant_pin": settings.serdipay_pin,
        "clientPhone": phone,
        "amount": amount,
        "currency": currency,
        "telecom": telecom,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": f"Bearer {access_token}"}
    response = _serdipay_request("POST", PAYMENT_URL, json=payload, headers=headers, timeout=25)
    try:
        response_payload = response.json()
    except ValueError:
        response_payload = {"raw_response": response.text}

    return {
        "reference": reference,
        "token_response": sanitized_token_data,
        "payment_payload_keys_sent": sorted(payload.keys()),
        "serdipay_status_code": response.status_code,
        "serdipay_response": response_payload,
    }
