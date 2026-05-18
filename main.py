from fastapi import FastAPI, Request
import requests
import os
import uuid

app = FastAPI()

SERDIPAY_API_ID = os.getenv("SERDIPAY_API_ID")
SERDIPAY_API_PASSWORD = os.getenv("SERDIPAY_API_PASSWORD")
SERDIPAY_MERCHANT_CODE = os.getenv("SERDIPAY_MERCHANT_CODE")
SERDIPAY_PIN = os.getenv("SERDIPAY_PIN")

TOKEN_URL = "https://serdipay.com/api/public-api/v1/merchant/get-token"
PAYMENT_URL = "https://serdipay.com/api/public-api/v1/merchant/payment-merchant"

@app.get("/")
async def home():
    return {"message": "Badiboss Pay API Running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

def get_token():
    payload = {
        "api_id": SERDIPAY_API_ID,
        "api_password": SERDIPAY_API_PASSWORD,
        "merchantCode": SERDIPAY_MERCHANT_CODE
    }

    response = requests.post(TOKEN_URL, json=payload)

    return {
        "status_code": response.status_code,
        "response": response.json()
    }

@app.post("/api/test-token")
async def test_token():
    return get_token()

@app.post("/api/test-payment")
async def test_payment(request: Request):
    body = await request.json()

    token_data = get_token()
    token_response = token_data.get("response", {})

    access_token = (
        token_response.get("token")
        or token_response.get("access_token")
        or token_response.get("accessToken")
    )

    reference = str(uuid.uuid4())

    payload = {
        "api_id": SERDIPAY_API_ID,
        "api_password": SERDIPAY_API_PASSWORD,
        "merchantCode": SERDIPAY_MERCHANT_CODE,
        "merchant_pin": SERDIPAY_PIN,
        "clientPhone": body.get("phone"),
        "amount": body.get("amount"),
        "currency": body.get("currency", "CDF"),
        "telecom": body.get("telecom", "AM")
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(
        PAYMENT_URL,
        json=payload,
        headers=headers
    )

    return {
        "reference": reference,
        "token_response": token_data,
        "payment_payload_sent": {
            "merchantCode": SERDIPAY_MERCHANT_CODE,
            "clientPhone": body.get("phone"),
            "amount": body.get("amount"),
            "currency": body.get("currency", "CDF"),
            "telecom": body.get("telecom", "AM")
        },
        "serdipay_status_code": response.status_code,
        "serdipay_response": response.json()
    }

@app.post("/serdipay/callback")
async def serdipay_callback(request: Request):
    data = await request.json()
    print("CALLBACK:", data)

    return {"success": True}