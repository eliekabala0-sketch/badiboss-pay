from fastapi import APIRouter, Request

from app.services.serdipay_service import create_test_payment_diagnostic, get_token

router = APIRouter(tags=["Legacy Compatibility"])


@router.post("/api/test-token")
def legacy_test_token():
    return get_token(sanitize=True, include_attempts=True)


@router.post("/api/test-payment")
async def legacy_test_payment(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    return create_test_payment_diagnostic(
        phone=body.get("clientPhone") or body.get("phone"),
        amount=body.get("amount"),
        currency=body.get("currency", "CDF"),
        telecom=body.get("telecom", "AM"),
    )


@router.post("/serdipay/callback")
async def legacy_serdipay_callback(request: Request):
    data = await request.json()
    return {"success": True, "received": data}
