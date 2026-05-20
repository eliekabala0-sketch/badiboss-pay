import json
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.security_log import SecurityLog
from app.models.webhook_log import WebhookLog


def _client_ip(request: Request) -> Optional[str]:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def log_security_event(
    db: Session,
    request: Request,
    event_type: str,
    severity: str = "info",
    actor: Optional[str] = None,
    app_id: Optional[str] = None,
    company_id: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    db.add(
        SecurityLog(
            event_type=event_type,
            severity=severity,
            actor=actor,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            app_id=app_id,
            company_id=company_id,
            details=details,
        )
    )
    db.commit()


def log_webhook_event(
    db: Session,
    direction: str,
    provider: str,
    event_type: Optional[str] = None,
    reference: Optional[str] = None,
    app_id: Optional[str] = None,
    company_id: Optional[str] = None,
    status_code: Optional[int] = None,
    payload: Optional[dict] = None,
    response_body: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    serialized_payload = json.dumps(payload, ensure_ascii=True) if payload is not None else None
    db.add(
        WebhookLog(
            direction=direction,
            provider=provider,
            event_type=event_type,
            reference=reference,
            app_id=app_id,
            company_id=company_id,
            status_code=status_code,
            payload=serialized_payload,
            response_body=response_body,
            error_message=error_message,
        )
    )
    db.commit()
