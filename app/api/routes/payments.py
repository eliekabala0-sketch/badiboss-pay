import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.deps import require_roles
from app.core.roles import AdminRole
from app.models.commission import Commission
from app.models.connected_app import ConnectedApp
from app.models.merchant_balance import MerchantBalance
from app.models.transaction import Transaction
from app.schemas.transactions import PaymentCreateRequest, PaymentStatusRequest
from app.services.commission_service import compute_commission_and_net
from app.services.serdipay_service import create_payment, get_egress_diagnostic, get_token
from app.services.tracking_service import collect_tracking_data

router = APIRouter(prefix="/payments", tags=["Payments"])


def _normalize_currency(currency: str) -> str:
    normalized = str(currency or "").upper()
    if normalized not in {"USD", "CDF"}:
        raise HTTPException(status_code=400, detail="currency must be USD or CDF")
    return normalized


def _provider_value(payload: dict, key: str):
    payment = payload.get("payment")
    if isinstance(payment, dict) and payment.get(key) not in (None, ""):
        return payment.get(key)
    return payload.get(key)


def _update_merchant_balance(db: Session, tx: Transaction) -> None:
    if tx.status != "success":
        return
    balance = (
        db.query(MerchantBalance)
        .filter(
            MerchantBalance.app_id == tx.app_id,
            MerchantBalance.company_id == tx.company_id,
            MerchantBalance.currency == tx.currency,
        )
        .first()
    )
    if not balance:
        balance = MerchantBalance(
            app_id=tx.app_id,
            company_id=tx.company_id,
            available_balance=0.0,
            pending_balance=0.0,
            currency=tx.currency,
        )
        db.add(balance)
    balance.available_balance += tx.net_amount


@router.post("/create")
def create_payment_endpoint(payload: PaymentCreateRequest, request: Request, db: Session = Depends(get_db)):
    app = (
        db.query(ConnectedApp)
        .filter(
            ConnectedApp.app_id == payload.app_id,
            ConnectedApp.company_id == payload.company_id,
            ConnectedApp.api_key == payload.api_key,
            ConnectedApp.secret_key == payload.secret_key,
            ConnectedApp.api_key_active.is_(True),
            ConnectedApp.secret_key_active.is_(True),
            ConnectedApp.status == "active",
        )
        .first()
    )
    if not app:
        raise HTTPException(status_code=401, detail="Invalid app credentials")

    currency = _normalize_currency(payload.currency)
    provider_payload = create_payment(
        phone=payload.phone,
        amount=payload.amount,
        currency=currency,
        telecom=payload.telecom,
    )
    provider_response = provider_payload.get("serdipay_response", {})
    provider_status_code = provider_payload.get("serdipay_status_code", 500)
    provider_reference = str(
        _provider_value(provider_response, "transactionId") or _provider_value(provider_response, "reference") or ""
    )
    provider_session_id = _provider_value(provider_response, "sessionId")
    status_value = "pending"
    if provider_status_code in (200, 201):
        status_value = "success"
    elif provider_status_code >= 400:
        status_value = "failed"

    provider_fees = 0.0
    commission, net_amount = compute_commission_and_net(app, payload.amount, provider_fees=provider_fees)
    tracking = collect_tracking_data(request, source_application=payload.source_application or app.name)

    tx = Transaction(
        reference=provider_payload["reference"],
        app_id=payload.app_id,
        user_id=payload.user_id,
        payer_phone=payload.phone,
        company_id=payload.company_id,
        amount=payload.amount,
        currency=currency,
        status=status_value,
        provider="serdipay",
        provider_reference=provider_reference or None,
        provider_session_id=str(provider_session_id) if provider_session_id not in (None, "") else None,
        raw_payload=json.dumps(provider_response, ensure_ascii=True),
        fees=provider_fees,
        commission=commission,
        net_amount=net_amount,
        payment_method=payload.payment_method,
        public_ip=tracking["public_ip"],
        country=tracking["country"],
        city=tracking["city"],
        region=tracking["region"],
        isp=tracking["isp"],
        device=tracking["device"],
        browser=tracking["browser"],
        operating_system=tracking["operating_system"],
        device_type=tracking["device_type"],
        source_application=tracking["source_application"],
    )
    db.add(tx)
    if commission > 0 and status_value == "success":
        db.add(
            Commission(
                app_id=payload.app_id,
                company_id=payload.company_id,
                transaction_reference=tx.reference,
                commission_type=app.commission_type,
                commission_value=app.commission_value,
                amount_collected=commission,
                currency=currency,
            )
        )
    _update_merchant_balance(db, tx)
    db.commit()
    db.refresh(tx)

    return {
        "transaction_id": tx.id,
        "reference": tx.reference,
        "status": tx.status,
        "provider": tx.provider,
        "provider_response": provider_response,
    }


@router.post("/status")
def payment_status(payload: PaymentStatusRequest, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.reference == payload.reference).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {
        "reference": tx.reference,
        "status": tx.status,
        "provider_reference": tx.provider_reference,
        "provider_session_id": tx.provider_session_id,
        "currency": tx.currency,
    }


@router.post("/test-token")
def test_token():
    return get_token(sanitize=True, include_attempts=True)


@router.get("/serdipay/egress")
def serdipay_egress(_=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN))):
    return get_egress_diagnostic()
