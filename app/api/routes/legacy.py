from fastapi import APIRouter, Request

from app.services.serdipay_service import create_payment, get_token

router = APIRouter(tags=["Legacy Compatibility"])


@router.post("/api/test-token")
def legacy_test_token():
    return get_token(sanitize=True)


@router.post("/api/test-payment")
async def legacy_test_payment(request: Request):
    body = await request.json()
    return create_payment(
        phone=body.get("phone"),
        amount=body.get("amount"),
        currency=body.get("currency", "CDF"),
        telecom=body.get("telecom", "AM"),
    )


@router.post("/serdipay/callback")
async def legacy_serdipay_callback(request: Request):
    data = await request.json()
    return {"success": True, "received": data}
