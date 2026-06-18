from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.transaction import Transaction
from app.services.client_callback_service import send_client_callback
from app.services.serdipay_callback_service import process_serdipay_callback
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
        currency=body.get("currency"),
        telecom=body.get("telecom", "AM"),
    )


@router.post("/serdipay/callback")
async def legacy_serdipay_callback(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    result = process_serdipay_callback(db, data if isinstance(data, dict) else {"payload": data})
    tx = db.query(Transaction).filter(Transaction.reference == result["transaction_reference"]).first()
    if tx:
        send_client_callback(db, tx)
    return {**result, "received": data}
