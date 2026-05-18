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
    return {
        "message": "Badiboss Pay API Running"
    }

@app.get("/health")
async def health():
    return {
        "status": "ok"
    }

def get_token():

    payload = {
        "api_id": SERDIPAY_API_ID,
        "api_password": SERDIPAY_API_PASSWORD
    }

    response = requests.post(TOKEN_URL, json=payload)

    return response.json()

@app.post("/api/test-token")
async def test_token():

    token_response = get_token()

    return token_response

@app.post("/api/test-payment")
async def test_payment(request: Request):

    body = await request.json()

    token_data = get_token()

    access_token = token_data.get("token")

    reference = str(uuid.uuid4())

    payload = {
        "merchantCode": SERDIPAY_MERCHANT_CODE,
        "merchant_pin": SERDIPAY_PIN,
        "api_id": SERDIPAY_API_ID,
        "api_password": SERDIPAY_API_PASSWORD,
        "amount": body.get("amount"),
        "currency": body.get("currency", "USD"),
        "telephone": body.get("phone"),
        "reference": reference,
        "description": "Badiboss Pay Test"
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.post(
        PAYMENT_URL,
        json=payload,
        headers=headers
    )

    return {
        "reference": reference,
        "serdipay_response": response.json()
    }

@app.post("/serdipay/callback")
async def serdipay_callback(request: Request):

    data = await request.json()

    print("CALLBACK:", data)

    return {
        "success": True
    }