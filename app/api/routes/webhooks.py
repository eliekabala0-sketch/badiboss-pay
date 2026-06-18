from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.transaction import Transaction
from app.models.webhook_log import WebhookLog
from app.services.client_callback_service import send_client_callback
from app.services.serdipay_callback_service import process_serdipay_callback
from app.services.serdipay_service import get_token

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/serdipay")
async def serdipay_callback(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    result = process_serdipay_callback(db, payload if isinstance(payload, dict) else {"payload": payload})
    tx = db.query(Transaction).filter(Transaction.reference == result["transaction_reference"]).first()
    if tx:
        send_client_callback(db, tx)
    return result


@router.get("/history")
def webhook_history(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.VIEWER)),
):
    return db.query(WebhookLog).order_by(WebhookLog.created_at.desc()).limit(500).all()


@router.get("/status")
def webhook_status(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.VIEWER)),
):
    total = db.query(func.count(WebhookLog.id)).scalar() or 0
    success = db.query(func.count(WebhookLog.id)).filter(WebhookLog.status_code < 400).scalar() or 0
    failed = (
        db.query(func.count(WebhookLog.id))
        .filter((WebhookLog.status_code >= 400) | (WebhookLog.error_message.isnot(None)))
        .scalar()
        or 0
    )
    return {"total": total, "success": success, "failed": failed}


@router.get("/serdipay/validation-summary")
def serdipay_validation_summary(
    transaction_id: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    token_result = get_token(sanitize=True)
    token_ok = bool(token_result.get("token_present"))

    tx_query = db.query(Transaction).filter(Transaction.provider == "serdipay")
    if transaction_id or session_id:
        identifiers = [value for value in (transaction_id, session_id) if value]
        tx_query = tx_query.filter(
            or_(
                Transaction.reference.in_(identifiers),
                Transaction.provider_reference.in_(identifiers),
                Transaction.provider_session_id.in_(identifiers),
            )
        )
    transaction = tx_query.order_by(Transaction.created_at.desc()).first()

    webhook_query = db.query(WebhookLog).filter(WebhookLog.provider == "serdipay", WebhookLog.direction == "INBOUND")
    if transaction:
        webhook_query = webhook_query.filter(WebhookLog.reference == transaction.reference)
    webhook = webhook_query.order_by(WebhookLog.created_at.desc()).first()

    is_callback_test = bool(transaction and transaction.payment_method == "callback_test")
    payment_request_ok = bool(transaction and (transaction.provider_reference or transaction.provider_session_id))
    callback_ok = bool(webhook and webhook.status_code and webhook.status_code < 400)
    transaction_visible_ok = bool(transaction)

    return {
        "token_ok": token_ok,
        "payment_request_ok": payment_request_ok,
        "callback_ok": callback_ok,
        "transaction_visible_ok": transaction_visible_ok,
        "ready_for_serdipay_review": all([token_ok, payment_request_ok, callback_ok, transaction_visible_ok]),
        "token_status_code": token_result.get("status_code"),
        "transaction": None
        if not transaction
        else {
            "reference": transaction.reference,
            "transactionId": transaction.provider_reference,
            "sessionId": transaction.provider_session_id,
            "status": transaction.status,
            "status_display": "success / paye" if transaction.status == "success" else transaction.status,
            "provider": transaction.provider,
            "currency": transaction.currency or "UNKNOWN",
            "amount": None if is_callback_test else transaction.amount,
            "amount_display": "N/A" if is_callback_test else f"{transaction.amount} {transaction.currency}",
            "source": transaction.source_application,
            "is_callback_test": is_callback_test,
        },
        "webhook": None
        if not webhook
        else {
            "id": webhook.id,
            "reference": webhook.reference,
            "status_code": webhook.status_code,
            "payload": webhook.payload,
            "created_at": webhook.created_at,
        },
    }


@router.get("/errors")
def webhook_errors(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    return (
        db.query(WebhookLog)
        .filter((WebhookLog.status_code >= 400) | (WebhookLog.error_message.isnot(None)))
        .order_by(WebhookLog.created_at.desc())
        .limit(300)
        .all()
    )


@router.post("/retry/{log_id}")
def retry_webhook(
    log_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    webhook_log = db.query(WebhookLog).filter(WebhookLog.id == log_id).first()
    if not webhook_log:
        raise HTTPException(status_code=404, detail="Webhook log not found")
    if not webhook_log.reference:
        raise HTTPException(status_code=400, detail="Webhook reference missing")

    tx = db.query(Transaction).filter(Transaction.reference == webhook_log.reference).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found for retry")

    send_client_callback(db, tx)
    return {"success": True, "reference": tx.reference}


@router.post("/client/{app_id}")
def debug_client_callback(app_id: str):
    raise HTTPException(status_code=501, detail=f"Debug callback endpoint not implemented for {app_id}")
