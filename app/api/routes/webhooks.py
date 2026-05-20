import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.core.config import settings
from app.models.connected_app import ConnectedApp
from app.models.transaction import Transaction
from app.models.webhook_log import WebhookLog
from app.services.audit_service import log_webhook_event

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/serdipay")
async def serdipay_callback(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    reference = payload.get("reference") or payload.get("client_reference")
    status_value = payload.get("status", "").lower()
    log_webhook_event(
        db,
        direction="INBOUND",
        provider="serdipay",
        event_type=payload.get("event_type") or "payment_update",
        reference=reference,
        status_code=200,
        payload=payload,
    )

    tx = db.query(Transaction).filter(Transaction.reference == reference).first() if reference else None
    if tx:
        if status_value in {"success", "failed", "cancelled", "pending"}:
            tx.status = status_value
        tx.provider_reference = str(payload.get("provider_reference") or tx.provider_reference or "")
        db.commit()
        db.refresh(tx)
        _send_client_callback(db, tx)

    return {"success": True}


def _send_client_callback(db: Session, transaction: Transaction) -> None:
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == transaction.app_id).first()
    if not app or not app.callback_url:
        return

    callback_payload = {
        "reference": transaction.reference,
        "status": transaction.status,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "provider_reference": transaction.provider_reference,
    }
    headers = {"X-Badiboss-App-Id": app.app_id, "X-Badiboss-Api-Key": app.api_key}
    try:
        response = requests.post(
            app.callback_url,
            json=callback_payload,
            headers=headers,
            timeout=settings.client_callback_timeout_seconds,
        )
        log_webhook_event(
            db,
            direction="OUTBOUND",
            provider="badiboss_pay",
            event_type="client_callback",
            reference=transaction.reference,
            app_id=transaction.app_id,
            company_id=transaction.company_id,
            status_code=response.status_code,
            payload=callback_payload,
            response_body=response.text[:2000],
        )
    except Exception:
        log_webhook_event(
            db,
            direction="OUTBOUND",
            provider="badiboss_pay",
            event_type="client_callback",
            reference=transaction.reference,
            app_id=transaction.app_id,
            company_id=transaction.company_id,
            payload=callback_payload,
            error_message="Client callback failed",
        )


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

    _send_client_callback(db, tx)
    return {"success": True, "reference": tx.reference}


@router.post("/client/{app_id}")
def debug_client_callback(app_id: str):
    raise HTTPException(status_code=501, detail=f"Debug callback endpoint not implemented for {app_id}")
