from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.transaction import Transaction
from app.models.webhook_log import WebhookLog
from app.services.client_callback_service import send_client_callback
from app.services.serdipay_callback_service import process_serdipay_callback

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
