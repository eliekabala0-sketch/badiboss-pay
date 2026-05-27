import uuid
from typing import Any

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


def get_egress_diagnostic() -> dict:
    proxies = _serdipay_proxy_config()
    diagnostic = {
        "proxy_configured": bool(proxies),
        "expected_outbound_ip": settings.serdipay_expected_outbound_ip,
        "observed_outbound_ip": None,
        "matches_expected_ip": False,
        "check_status_code": None,
        "error": None,
    }
    try:
        response = _serdipay_request("GET", settings.serdipay_egress_check_url, timeout=15)
        diagnostic["check_status_code"] = response.status_code
        payload = response.json()
        observed_ip = payload.get("ip")
        diagnostic["observed_outbound_ip"] = observed_ip
        diagnostic["matches_expected_ip"] = observed_ip == settings.serdipay_expected_outbound_ip
    except Exception as exc:
        diagnostic["error"] = exc.__class__.__name__
    return diagnostic


def get_token() -> dict:
    payload = {
        "api_id": settings.serdipay_api_id,
        "api_password": settings.serdipay_api_password,
        "merchantCode": settings.serdipay_merchant_code,
    }
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
