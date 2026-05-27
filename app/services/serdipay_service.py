import uuid
import socket
from typing import Any
from urllib.parse import urlparse

import requests

from app.core.config import settings

TOKEN_URL = "https://serdipay.com/api/public-api/v1/merchant/get-token"
PAYMENT_URL = "https://serdipay.com/api/public-api/v1/merchant/payment-merchant"


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


def _token_payload() -> dict:
    return {
        "api_id": settings.serdipay_api_id,
        "api_password": settings.serdipay_api_password,
        "merchantCode": settings.serdipay_merchant_code,
    }


def _safe_token_test(proxies: dict[str, str] | None = None) -> dict:
    try:
        kwargs: dict[str, Any] = {"json": _token_payload(), "timeout": 20}
        if proxies:
            kwargs["proxies"] = proxies
        response = requests.post(TOKEN_URL, **kwargs)
        try:
            payload = response.json()
            response_keys = sorted(payload.keys()) if isinstance(payload, dict) else []
            token_present = any(key in payload for key in ("token", "access_token", "accessToken")) if isinstance(payload, dict) else False
            message = payload.get("message") or payload.get("detail") if isinstance(payload, dict) else None
        except ValueError:
            response_keys = []
            token_present = False
            message = response.text[:160]
        return {
            "status_code": response.status_code,
            "token_present": token_present,
            "response_keys": response_keys,
            "message": message,
            "error": None,
        }
    except Exception as exc:
        return {
            "status_code": None,
            "token_present": False,
            "response_keys": [],
            "message": None,
            "error": exc.__class__.__name__,
        }


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


def get_token() -> dict:
    payload = _token_payload()
    response = _serdipay_request("POST", TOKEN_URL, json=payload, timeout=20)
    data = {}
    try:
        data = response.json()
    except ValueError:
        data = {"raw_response": response.text}
    return {"status_code": response.status_code, "response": data}


def create_payment(phone: str, amount: float, currency: str = "CDF", telecom: str = "AM") -> dict:
    token_data = get_token()
    token_response = token_data.get("response", {})
    access_token = (
        token_response.get("token")
        or token_response.get("access_token")
        or token_response.get("accessToken")
    )
    reference = str(uuid.uuid4())
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
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    response = _serdipay_request("POST", PAYMENT_URL, json=payload, headers=headers, timeout=25)
    try:
        response_payload = response.json()
    except ValueError:
        response_payload = {"raw_response": response.text}

    return {
        "reference": reference,
        "token_response": token_data,
        "payment_payload_sent": payload,
        "serdipay_status_code": response.status_code,
        "serdipay_response": response_payload,
    }
