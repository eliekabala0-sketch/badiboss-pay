from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.commission import Commission
from app.models.connected_app import ConnectedApp
from app.models.transaction import Transaction
from app.schemas.transactions import AppPaymentRequest
from app.services.commission_service import compute_commission_and_net
from app.services.serdipay_service import create_payment
from app.services.tracking_service import collect_tracking_data

router = APIRouter(prefix="/api/v1/apps", tags=["Public App Payments"])


def _normalize_currency(currency: str) -> str:
    value = str(currency or "").upper()
    if value not in {"USD", "CDF"}:
        raise HTTPException(status_code=400, detail="currency must be USD or CDF")
    return value


def _provider_value(payload: dict, key: str):
    payment = payload.get("payment")
    if isinstance(payment, dict) and payment.get(key) not in (None, ""):
        return payment.get(key)
    return payload.get(key)


def _get_authenticated_app(
    db: Session,
    app_slug: str,
    api_key: Optional[str],
    api_secret: Optional[str],
) -> ConnectedApp:
    app = (
        db.query(ConnectedApp)
        .filter(
            ConnectedApp.app_slug == app_slug,
            ConnectedApp.api_key == api_key,
            ConnectedApp.secret_key == api_secret,
            ConnectedApp.api_key_active.is_(True),
            ConnectedApp.secret_key_active.is_(True),
        )
        .first()
    )
    if not app:
        raise HTTPException(status_code=401, detail="Invalid app credentials")
    if app.status != "active":
        raise HTTPException(status_code=403, detail="Application inactive")
    return app


async def _parse_app_payment_request(request: Request) -> AppPaymentRequest:
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(status_code=422, detail="JSON body is required")
    try:
        decoded = json.loads(raw_body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=422, detail="Invalid JSON body")
    if isinstance(decoded, dict) and "body" in decoded and isinstance(decoded["body"], (dict, str)):
        decoded = decoded["body"]
        if isinstance(decoded, str):
            try:
                decoded = json.loads(decoded)
            except json.JSONDecodeError:
                raise HTTPException(status_code=422, detail="Invalid JSON body wrapper")
    if not isinstance(decoded, dict):
        raise HTTPException(status_code=422, detail="JSON object body is required")
    try:
        if hasattr(AppPaymentRequest, "model_validate"):
            return AppPaymentRequest.model_validate(decoded)
        return AppPaymentRequest.parse_obj(decoded)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())


def _find_transaction(db: Session, app: ConnectedApp, transaction_id: str) -> Transaction | None:
    query = db.query(Transaction).filter(Transaction.app_id == app.app_id)
    if transaction_id.isdigit():
        found = query.filter(Transaction.id == int(transaction_id)).first()
        if found:
            return found
    return query.filter(Transaction.reference == transaction_id).first()


@router.post("/{app_slug}/payments")
async def create_app_payment(
    app_slug: str,
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    x_api_secret: Optional[str] = Header(default=None, alias="X-API-Secret"),
):
    payload = await _parse_app_payment_request(request)
    return create_app_payment_from_payload(
        app_slug=app_slug,
        payload=payload,
        request=request,
        db=db,
        x_api_key=x_api_key,
        x_api_secret=x_api_secret,
    )


def create_app_payment_from_payload(
    app_slug: str,
    payload: AppPaymentRequest,
    request: Request,
    db: Session,
    x_api_key: Optional[str],
    x_api_secret: Optional[str],
):
    app = _get_authenticated_app(db, app_slug, x_api_key, x_api_secret)
    request.state.log_app_id = app.app_id
    request.state.log_company_id = app.company_id
    existing = db.query(Transaction).filter(Transaction.reference == payload.reference).first()
    if existing:
        raise HTTPException(status_code=409, detail="reference already exists")

    currency = _normalize_currency(payload.currency)
    commission, net_amount = compute_commission_and_net(app, payload.amount, provider_fees=0.0)
    callback_url = payload.callback_url or app.callback_url or None
    tracking = collect_tracking_data(request, source_application=app.name)
    tx = Transaction(
        reference=payload.reference,
        app_id=app.app_id,
        user_id=payload.customer_id,
        customer_name=payload.customer_name,
        payer_phone=payload.clientPhone,
        company_id=app.company_id,
        amount=payload.amount,
        currency=currency,
        status="pending",
        provider="serdipay",
        raw_payload=json.dumps({"request": payload.model_dump(mode="json")}, ensure_ascii=True),
        callback_url=callback_url,
        metadata_json=json.dumps(payload.metadata, ensure_ascii=True),
        fees=0.0,
        commission=commission,
        net_amount=net_amount,
        payment_method=payload.telecom,
        public_ip=tracking["public_ip"],
        country=tracking["country"],
        city=tracking["city"],
        region=tracking["region"],
        isp=tracking["isp"],
        device=tracking["device"],
        browser=tracking["browser"],
        operating_system=tracking["operating_system"],
        device_type=tracking["device_type"],
        source_application="API app",
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    provider_payload = create_payment(
        phone=payload.clientPhone,
        amount=payload.amount,
        currency=currency,
        telecom=payload.telecom,
    )
    provider_response = provider_payload.get("serdipay_response", {})
    if not isinstance(provider_response, dict):
        provider_response = {"raw_response": provider_response}
    provider_status_code = provider_payload.get("serdipay_status_code", 500)
    provider_reference = str(
        _provider_value(provider_response, "transactionId") or _provider_value(provider_response, "reference") or ""
    )
    provider_session_id = _provider_value(provider_response, "sessionId")
    tx.provider_reference = provider_reference or None
    tx.provider_session_id = str(provider_session_id) if provider_session_id not in (None, "") else None
    tx.raw_payload = json.dumps(
        {
            "request": payload.model_dump(mode="json"),
            "provider_status_code": provider_status_code,
            "provider_response": provider_response,
        },
        ensure_ascii=True,
    )
    if provider_status_code >= 400 and provider_response.get("message") == "SerdiPay token unavailable":
        tx.status = "failed"
    if commission > 0 and tx.status == "success":
        db.add(
            Commission(
                app_id=app.app_id,
                company_id=app.company_id,
                transaction_reference=tx.reference,
                commission_type=app.commission_type,
                commission_value=app.commission_value,
                amount_collected=commission,
                currency=currency,
            )
        )
    db.commit()
    db.refresh(tx)

    return {
        "success": tx.status != "failed",
        "transaction_id": str(tx.id),
        "reference": tx.reference,
        "status": tx.status,
        "provider": "serdipay",
        "message": "Payment request sent" if tx.status != "failed" else "Payment request failed",
        "currency": tx.currency,
        "amount": tx.amount,
        "provider_status_code": provider_status_code,
        "provider_response": provider_response,
    }


@router.get("/{app_slug}/payments/{transaction_id}/status")
def get_app_payment_status(
    app_slug: str,
    transaction_id: str,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    x_api_secret: Optional[str] = Header(default=None, alias="X-API-Secret"),
):
    app = _get_authenticated_app(db, app_slug, x_api_key, x_api_secret)
    tx = _find_transaction(db, app, transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "transaction_id": str(tx.id),
        "reference": tx.reference,
        "status": tx.status,
        "amount": tx.amount,
        "currency": tx.currency,
        "telecom": tx.payment_method,
        "provider_transaction_id": tx.provider_reference,
        "provider_session_id": tx.provider_session_id,
        "updated_at": tx.updated_at.isoformat(),
    }
