import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.connected_app import ConnectedApp
from app.models.transaction import Transaction
from app.services.audit_service import log_webhook_event


def send_client_callback(db: Session, transaction: Transaction) -> None:
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == transaction.app_id).first()
    if not app or not app.callback_url:
        return

    callback_payload = {
        "reference": transaction.reference,
        "status": transaction.status,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "provider_reference": transaction.provider_reference,
        "provider_session_id": transaction.provider_session_id,
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
