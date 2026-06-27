import hashlib
import hmac
import json
import time

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.connected_app import ConnectedApp
from app.models.transaction import Transaction
from app.services.audit_service import log_webhook_event


def send_client_callback(db: Session, transaction: Transaction) -> None:
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == transaction.app_id).first()
    callback_url = transaction.callback_url or (app.callback_url if app else None)
    if not app or not callback_url:
        return

    metadata = {}
    if transaction.metadata_json:
        try:
            metadata = json.loads(transaction.metadata_json)
        except ValueError:
            metadata = {}
    event_name = "payment.success" if transaction.status == "success" else f"payment.{transaction.status}"
    callback_payload = {
        "event": event_name,
        "app_id": app.app_id,
        "reference": transaction.reference,
        "transaction_id": str(transaction.id),
        "status": transaction.status,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "telecom": transaction.payment_method,
        "provider": transaction.provider,
        "provider_transaction_id": transaction.provider_reference,
        "provider_session_id": transaction.provider_session_id,
        "metadata": metadata,
    }
    timestamp = str(int(time.time()))
    body = json.dumps(callback_payload, separators=(",", ":"), ensure_ascii=True)
    signature = hmac.new(
        app.webhook_secret.encode("utf-8"),
        f"{timestamp}.{body}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Badiboss-App-Id": app.app_id,
        "X-Badiboss-Timestamp": timestamp,
        "X-Badiboss-Signature": signature,
    }
    try:
        response = requests.post(
            callback_url,
            data=body,
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
            payload={"url": callback_url, "body": callback_payload},
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
            payload={"url": callback_url, "body": callback_payload},
            error_message="Client callback failed",
        )
