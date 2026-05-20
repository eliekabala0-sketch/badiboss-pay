import uuid

import requests

from app.core.config import settings

TOKEN_URL = "https://serdipay.com/api/public-api/v1/merchant/get-token"
PAYMENT_URL = "https://serdipay.com/api/public-api/v1/merchant/payment-merchant"


def get_token() -> dict:
    payload = {
        "api_id": settings.serdipay_api_id,
        "api_password": settings.serdipay_api_password,
        "merchantCode": settings.serdipay_merchant_code,
    }
    response = requests.post(TOKEN_URL, json=payload, timeout=20)
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
    response = requests.post(PAYMENT_URL, json=payload, headers=headers, timeout=25)
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
