from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.commission import Commission
from app.models.connected_app import ConnectedApp
from app.models.merchant_balance import MerchantBalance
from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.models.withdrawal import Withdrawal
from app.services.audit_service import log_webhook_event


def _nested(payload: dict[str, Any], key: str) -> Any:
    payment = payload.get("payment")
    if isinstance(payment, dict) and payment.get(key) not in (None, ""):
        return payment.get(key)
    return payload.get(key)


def _normalized_status(payload: dict[str, Any]) -> str:
    value = _nested(payload, "status")
    if isinstance(value, int):
        return "success" if value == 200 else "failed"
    text = str(value or "").lower()
    if text in {"success", "successful", "paid", "completed"}:
        return "success"
    if text in {"failed", "failure", "cancelled", "canceled", "error"}:
        return "failed"
    if text in {"pending", "processing"}:
        return "pending"
    return "pending"


def _normalized_currency(payload: dict[str, Any], fallback: str = "UNKNOWN") -> str:
    value = _nested(payload, "currency") or fallback
    text = str(value).upper()
    return text if text in {"USD", "CDF"} else "UNKNOWN"


def _payload_has_value(payload: dict[str, Any], key: str) -> bool:
    return _nested(payload, key) not in (None, "")


def _float_value(payload: dict[str, Any], key: str, fallback: float = 0.0) -> float:
    value = _nested(payload, key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _raw_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True)


def _callback_ids(payload: dict[str, Any]) -> dict[str, str | None]:
    transaction_id = _nested(payload, "transactionId") or _nested(payload, "provider_reference")
    session_id = _nested(payload, "sessionId")
    reference = payload.get("reference") or payload.get("client_reference") or session_id or transaction_id
    return {
        "transaction_id": str(transaction_id) if transaction_id not in (None, "") else None,
        "session_id": str(session_id) if session_id not in (None, "") else None,
        "reference": str(reference) if reference not in (None, "") else None,
    }


def _find_transaction(db: Session, ids: dict[str, str | None]) -> Transaction | None:
    candidates = [value for value in ids.values() if value]
    if not candidates:
        return None
    return (
        db.query(Transaction)
        .filter(
            or_(
                Transaction.reference.in_(candidates),
                Transaction.provider_reference.in_(candidates),
                Transaction.provider_session_id.in_(candidates),
            )
        )
        .first()
    )


def _find_withdrawal(db: Session, ids: dict[str, str | None]) -> Withdrawal | None:
    candidates = [value for value in ids.values() if value]
    if not candidates:
        return None
    return (
        db.query(Withdrawal)
        .filter(
            or_(
                Withdrawal.reference.in_(candidates),
                Withdrawal.provider_reference.in_(candidates),
            )
        )
        .with_for_update()
        .first()
    )


def _process_withdrawal_callback(
    db: Session,
    withdrawal: Withdrawal,
    ids: dict[str, str | None],
    callback_status: str,
) -> dict[str, Any]:
    previous_status = withdrawal.status
    if ids["transaction_id"]:
        withdrawal.provider_reference = ids["transaction_id"]
    elif ids["session_id"] and not withdrawal.provider_reference:
        withdrawal.provider_reference = ids["session_id"]
    if callback_status == "pending" and previous_status in {"pending", "processing"}:
        withdrawal.status = "processing"
    elif callback_status in {"success", "failed"} and previous_status in {"pending", "processing"}:
        balance = (
            db.query(MerchantBalance)
            .filter(
                MerchantBalance.app_id == withdrawal.app_id,
                MerchantBalance.company_id == withdrawal.company_id,
                MerchantBalance.currency == withdrawal.currency,
            )
            .with_for_update()
            .first()
        )
        if balance and balance.pending_balance >= withdrawal.amount:
            balance.pending_balance -= withdrawal.amount
            if callback_status == "failed":
                balance.available_balance += withdrawal.amount
        withdrawal.status = "completed" if callback_status == "success" else "failed"
        withdrawal.failure_reason = None if callback_status == "success" else "Reversement refuse ou annule par SerdiPay"
        withdrawal.processed_at = datetime.now(timezone.utc)
        existing_settlement = (
            db.query(Settlement)
            .filter(Settlement.withdrawal_reference == withdrawal.reference)
            .first()
        )
        if not existing_settlement:
            db.add(
                Settlement(
                    app_id=withdrawal.app_id,
                    company_id=withdrawal.company_id,
                    reference=f"set_{withdrawal.reference}",
                    amount=withdrawal.amount,
                    currency=withdrawal.currency,
                    status="completed" if callback_status == "success" else "failed",
                    withdrawal_reference=withdrawal.reference,
                    destination_type=withdrawal.destination_type,
                    provider_reference=withdrawal.provider_reference,
                    processed_at=withdrawal.processed_at,
                )
            )
    db.commit()
    return {
        "success": True,
        "action": "withdrawal_updated",
        "withdrawal_reference": withdrawal.reference,
        "status": withdrawal.status,
        "transaction_id": ids["transaction_id"],
        "session_id": ids["session_id"],
    }


def _ensure_serdipay_callback_app(db: Session) -> ConnectedApp:
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == "serdipay").first()
    if app:
        return app
    app = ConnectedApp(
        app_id="serdipay",
        app_slug="serdipay",
        company_id="serdipay",
        api_key="internal-serdipay-callback",
        secret_key="internal-serdipay-callback",
        webhook_secret="internal-serdipay-callback",
        name="SerdiPay callbacks",
        app_type="provider",
        callback_url="",
        status="active",
        api_key_active=False,
        secret_key_active=False,
        commission_type="none",
        commission_value=0.0,
    )
    db.add(app)
    db.flush()
    return app


def _credit_merchant_balance(db: Session, transaction: Transaction) -> None:
    if transaction.currency not in {"USD", "CDF"} or transaction.net_amount <= 0:
        return
    balance = (
        db.query(MerchantBalance)
        .filter(
            MerchantBalance.app_id == transaction.app_id,
            MerchantBalance.company_id == transaction.company_id,
            MerchantBalance.currency == transaction.currency,
        )
        .first()
    )
    if not balance:
        balance = MerchantBalance(
            app_id=transaction.app_id,
            company_id=transaction.company_id,
            available_balance=0.0,
            pending_balance=0.0,
            currency=transaction.currency,
        )
        db.add(balance)
    balance.available_balance += transaction.net_amount


def _record_commission(db: Session, transaction: Transaction) -> None:
    if transaction.commission <= 0 or transaction.currency not in {"USD", "CDF"}:
        return
    existing = (
        db.query(Commission)
        .filter(Commission.transaction_reference == transaction.reference)
        .first()
    )
    if existing:
        return
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == transaction.app_id).first()
    if not app:
        return
    db.add(
        Commission(
            app_id=transaction.app_id,
            company_id=transaction.company_id,
            transaction_reference=transaction.reference,
            commission_type=app.commission_type,
            commission_value=app.commission_value,
            amount_collected=transaction.commission,
            currency=transaction.currency,
        )
    )


def process_serdipay_callback(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    ids = _callback_ids(payload)
    status = _normalized_status(payload)
    raw_payload = _raw_payload(payload)
    callback_has_amount = _payload_has_value(payload, "amount")
    callback_has_currency = _payload_has_value(payload, "currency")

    transaction = _find_transaction(db, ids)
    if not transaction:
        withdrawal = _find_withdrawal(db, ids)
        if withdrawal:
            return _process_withdrawal_callback(db, withdrawal, ids, status)
    if transaction:
        previous_status = transaction.status
        transaction.status = status
        if ids["transaction_id"]:
            transaction.provider_reference = ids["transaction_id"]
        if ids["session_id"]:
            transaction.provider_session_id = ids["session_id"]
        transaction.raw_payload = raw_payload
        transaction.updated_at = datetime.now(timezone.utc)
        if transaction.app_id == "serdipay" and not callback_has_amount:
            transaction.payment_method = "callback_test"
            transaction.source_application = "SerdiPay callback test"
        if transaction.app_id == "serdipay" and not callback_has_currency:
            transaction.currency = "UNKNOWN"
        reference = transaction.reference
        app_id = transaction.app_id
        company_id = transaction.company_id
        action = "updated"
    else:
        callback_app = _ensure_serdipay_callback_app(db)
        reference = ids["session_id"] or ids["transaction_id"] or ids["reference"] or "serdipay-callback"
        amount = _float_value(payload, "amount", 0.0)
        fees = _float_value(payload, "fees", 0.0)
        commission = _float_value(payload, "commission", 0.0)
        net_amount = _float_value(payload, "net_amount", max(amount - fees - commission, 0.0))
        is_callback_test = not callback_has_amount
        transaction = Transaction(
            reference=reference,
            app_id=callback_app.app_id,
            user_id=ids["session_id"] or ids["transaction_id"] or "serdipay-callback",
            customer_name="SerdiPay callback",
            payer_phone=str(_nested(payload, "clientPhone") or _nested(payload, "phone") or ""),
            company_id=callback_app.company_id,
            amount=amount,
            currency=_normalized_currency(payload),
            status=status,
            provider="serdipay",
            provider_reference=ids["transaction_id"],
            provider_session_id=ids["session_id"],
            fees=fees,
            commission=commission,
            net_amount=net_amount,
            payment_method="callback_test" if is_callback_test else "mobile_money",
            source_application="SerdiPay callback test" if is_callback_test else "SerdiPay callback",
            raw_payload=raw_payload,
        )
        db.add(transaction)
        app_id = transaction.app_id
        company_id = transaction.company_id
        previous_status = None
        action = "created"

    if transaction.status == "success" and previous_status != "success":
        _record_commission(db, transaction)
        _credit_merchant_balance(db, transaction)

    db.commit()
    db.refresh(transaction)

    log_webhook_event(
        db,
        direction="INBOUND",
        provider="serdipay",
        event_type="payment_callback",
        reference=transaction.reference,
        app_id=app_id,
        company_id=company_id,
        status_code=200,
        payload=payload,
    )

    return {
        "success": True,
        "action": action,
        "transaction_reference": transaction.reference,
        "transaction_id": ids["transaction_id"],
        "session_id": ids["session_id"],
        "status": transaction.status,
    }
