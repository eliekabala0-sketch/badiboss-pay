from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.api_log import ApiLog
from app.models.failed_request import FailedRequest
from app.models.security_log import SecurityLog
from app.models.webhook_log import WebhookLog

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.get("/api")
def list_api_logs(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.VIEWER))):
    return db.query(ApiLog).order_by(ApiLog.created_at.desc()).limit(300).all()


@router.get("/webhooks")
def list_webhook_logs(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.VIEWER))):
    return db.query(WebhookLog).order_by(WebhookLog.created_at.desc()).limit(300).all()


@router.get("/security")
def list_security_logs(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN))):
    return db.query(SecurityLog).order_by(SecurityLog.created_at.desc()).limit(300).all()


@router.get("/failed-requests")
def list_failed_requests(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN))):
    return db.query(FailedRequest).order_by(FailedRequest.created_at.desc()).limit(300).all()
