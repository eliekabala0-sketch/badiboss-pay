from __future__ import annotations

import json

from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.api.deps import get_db, require_roles
from app.core.config import settings
from app.core.roles import AdminRole
from app.models.connected_app import ConnectedApp
from app.models.transaction import Transaction
from app.models.webhook_log import WebhookLog
from app.schemas.apps import ConnectedAppCreate, ConnectedAppResponse, ConnectedAppUpdate
from app.schemas.transactions import AppPaymentRequest
from app.models.subscription import Subscription
from app.api.routes.public_apps import create_app_payment
from app.utils.keys import generate_api_key, generate_app_suffix, generate_secret_key, generate_webhook_secret, slugify_app_name

router = APIRouter(prefix="/apps", tags=["Connected Apps"])


class AppTestPaymentRequest(BaseModel):
    clientPhone: str = Field(min_length=8, max_length=40)
    amount: float = Field(gt=0)
    currency: str
    telecom: str = "OM"
    description: str = "Test application"


def _public_origin() -> str:
    return f"https://{settings.badiboss_public_domain}"


def _mask_secret(value: Optional[str], visible: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return f"{value[:visible]}...{value[-4:]}"


def _unique_slug(db: Session, name: str) -> str:
    base_slug = slugify_app_name(name)
    slug = base_slug
    counter = 2
    while db.query(ConnectedApp).filter(ConnectedApp.app_slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def _unique_app_id(db: Session, slug: str) -> str:
    base_app_id = f"app_{slug.replace('-', '_')}"
    app_id = f"{base_app_id}_{generate_app_suffix()}"
    while db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first():
        app_id = f"{base_app_id}_{generate_app_suffix()}"
    return app_id[:64]


def _app_metrics(db: Session, app_id: str) -> dict:
    total_usd = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.app_id == app_id, Transaction.currency == "USD", Transaction.status == "success")
        .scalar()
        or 0.0
    )
    total_cdf = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.app_id == app_id, Transaction.currency == "CDF", Transaction.status == "success")
        .scalar()
        or 0.0
    )
    status_rows = (
        db.query(Transaction.status, func.count(Transaction.id))
        .filter(Transaction.app_id == app_id)
        .group_by(Transaction.status)
        .all()
    )
    status_counts = {"success": 0, "failed": 0, "pending": 0}
    for status_value, count_value in status_rows:
        key = str(status_value or "pending").lower()
        if key in {"cancelled", "canceled", "error"}:
            key = "failed"
        if key not in status_counts:
            key = "pending"
        status_counts[key] += int(count_value or 0)
    return {
        "transactions_count": sum(status_counts.values()),
        "total_usd": float(total_usd),
        "total_cdf": float(total_cdf),
        "success_count": status_counts["success"],
        "failed_count": status_counts["failed"],
        "pending_count": status_counts["pending"],
    }


def _app_response(
    db: Session,
    app: ConnectedApp,
    reveal_api_secret: bool = False,
    reveal_webhook_secret: bool = False,
) -> dict:
    origin = _public_origin()
    payment_url = f"{origin}/api/v1/apps/{app.app_slug}/payments"
    status_url = f"{origin}/api/v1/apps/{app.app_slug}/payments/{{transaction_id}}/status"
    return {
        "id": app.id,
        "app_id": app.app_id,
        "app_slug": app.app_slug,
        "company_id": app.company_id,
        "api_key": app.api_key,
        "secret_key": app.secret_key if reveal_api_secret else _mask_secret(app.secret_key),
        "webhook_secret": app.webhook_secret if reveal_webhook_secret else _mask_secret(app.webhook_secret),
        "name": app.name,
        "app_type": app.app_type,
        "callback_url": app.callback_url or "",
        "status": app.status,
        "api_key_active": app.api_key_active,
        "secret_key_active": app.secret_key_active,
        "commission_type": app.commission_type,
        "commission_value": app.commission_value,
        "created_at": app.created_at,
        "payment_url": payment_url,
        "status_url": status_url,
        "callback_badiboss_pay": f"{origin}/serdipay/callback",
        "api_secret_once": app.secret_key if reveal_api_secret else None,
        "webhook_secret_once": app.webhook_secret if reveal_webhook_secret else None,
        **_app_metrics(db, app.app_id),
    }


def _normalized_commission_value(commission_type: str, commission_value: float) -> float:
    return 0.0 if commission_type == "none" else commission_value


@router.get("", response_model=list[ConnectedAppResponse])
def list_apps(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.VIEWER))):
    apps = db.query(ConnectedApp).order_by(ConnectedApp.created_at.desc()).all()
    return [_app_response(db, app) for app in apps]


@router.post("/create", response_model=ConnectedAppResponse, status_code=status.HTTP_201_CREATED)
def create_app(
    payload: ConnectedAppCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    app_slug = _unique_slug(db, payload.name)
    app_id = _unique_app_id(db, app_slug)

    app = ConnectedApp(
        app_id=app_id,
        app_slug=app_slug,
        company_id=payload.company_id,
        api_key=generate_api_key(),
        secret_key=generate_secret_key(),
        webhook_secret=generate_webhook_secret(),
        name=payload.name,
        app_type=payload.app_type,
        callback_url=payload.callback_url or "",
        status=payload.status,
        commission_type=payload.commission_type,
        commission_value=_normalized_commission_value(payload.commission_type, payload.commission_value),
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _app_response(db, app, reveal_api_secret=True, reveal_webhook_secret=True)


@router.patch("/{app_id}", response_model=ConnectedAppResponse)
def update_app(
    app_id: str,
    payload: ConnectedAppUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application introuvable")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(app, field, value)
    if app.commission_type == "none":
        app.commission_value = 0.0
    db.commit()
    db.refresh(app)
    return _app_response(db, app)


@router.patch("/{app_id}/status")
def update_app_status(
    app_id: str,
    status_value: str,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application introuvable")
    app.status = status_value
    db.commit()
    db.refresh(app)
    return _app_response(db, app)


@router.patch("/{app_id}/keys")
def toggle_app_keys(
    app_id: str,
    api_key_active: Optional[bool] = None,
    secret_key_active: Optional[bool] = None,
    regenerate: bool = False,
    target: str = "all",
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application introuvable")
    if api_key_active is not None:
        app.api_key_active = api_key_active
    if secret_key_active is not None:
        app.secret_key_active = secret_key_active
    if regenerate and target in {"all", "api"}:
        app.api_key = generate_api_key()
        app.secret_key = generate_secret_key()
        app.api_key_active = True
        app.secret_key_active = True
    if regenerate and target in {"all", "webhook"}:
        app.webhook_secret = generate_webhook_secret()
    db.commit()
    db.refresh(app)
    return _app_response(
        db,
        app,
        reveal_api_secret=regenerate and target in {"all", "api"},
        reveal_webhook_secret=regenerate and target in {"all", "webhook"},
    )


@router.get("/{app_id}/integration-guide")
def integration_guide(
    app_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.VIEWER)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application introuvable")
    app_data = _app_response(db, app)
    callback_example = {
        "event": "payment.success",
        "app_id": app.app_id,
        "reference": "DISC-2026-000001",
        "transaction_id": "1",
        "status": "success",
        "amount": 5,
        "currency": "USD",
        "telecom": "OM",
        "provider": "serdipay",
        "provider_transaction_id": "SERDIPAY-TX",
        "provider_session_id": "SERDIPAY-SESSION",
        "metadata": {"plan": "premium", "duration": "monthly"},
    }
    return {
        "app_name": app.name,
        "app_slug": app.app_slug,
        "app_id": app.app_id,
        "api_key": app.api_key,
        "payment_url": app_data["payment_url"],
        "status_url": app_data["status_url"],
        "callback_badiboss_pay": app_data["callback_badiboss_pay"],
        "request_format": {
            "reference": "DISC-2026-000001",
            "customer_id": "user_001",
            "customer_name": "Nom client",
            "clientPhone": "243897970873",
            "amount": 5,
            "currency": "USD",
            "telecom": "OM",
            "description": "Abonnement Premium Decouverte",
            "callback_url": app.callback_url,
            "metadata": {"plan": "premium", "duration": "monthly"},
        },
        "powershell_example": (
            f"Invoke-RestMethod -Method Post -Uri '{app_data['payment_url']}' "
            "-Headers @{ 'X-API-Key' = '<api_key>'; 'X-API-Secret' = '<api_secret>' } "
            "-ContentType 'application/json' -Body '<json_body>'"
        ),
        "javascript_fetch_example": (
            f"fetch('{app_data['payment_url']}', "
            "{ method: 'POST', headers: { 'Content-Type': 'application/json', "
            "'X-API-Key': '<api_key>', 'X-API-Secret': '<api_secret>' }, body: JSON.stringify(payload) })"
        ),
        "php_example": "$response = file_get_contents($paymentUrl, false, stream_context_create(['http' => ['method' => 'POST', 'header' => \"Content-Type: application/json\\r\\nX-API-Key: <api_key>\\r\\nX-API-Secret: <api_secret>\", 'content' => json_encode($payload)]]));",
        "laravel_example": "Http::withHeaders(['X-API-Key' => '<api_key>', 'X-API-Secret' => '<api_secret>'])->post($paymentUrl, $payload);",
        "flutter_dart_example": "await http.post(Uri.parse(paymentUrl), headers: {'Content-Type': 'application/json', 'X-API-Key': apiKey, 'X-API-Secret': apiSecret}, body: jsonEncode(payload));",
        "python_requests_example": "requests.post(payment_url, headers={'X-API-Key': api_key, 'X-API-Secret': api_secret}, json=payload)",
        "callback_format": callback_example,
        "security_rules": [
            "Ne jamais exposer api_secret cote navigateur ou page publique.",
            "Verifier X-Badiboss-Signature avec webhook_secret et X-Badiboss-Timestamp.",
            "Garder une reference unique par paiement cote application cliente.",
        ],
        "telecom_codes": {
            "OM": "Orange Money",
            "AM": "Airtel Money",
            "MP": "M-Pesa / Vodacom",
            "Afrimoney": "A confirmer selon SerdiPay",
        },
        "observed_minimums": {"USD": 5, "CDF": 500},
    }


@router.post("/{app_id}/test-payment")
def test_connected_app(
    app_id: str,
    payload: AppTestPaymentRequest,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application introuvable")
    if app.status != "active":
        raise HTTPException(status_code=403, detail="Application inactive")
    app_payload = AppPaymentRequest(
        reference=f"TEST-{app.app_slug.upper()}-{generate_app_suffix().upper()}",
        customer_id="admin_test",
        customer_name="Admin Test",
        clientPhone=payload.clientPhone,
        amount=payload.amount,
        currency=payload.currency,
        telecom=payload.telecom,
        description=payload.description,
        metadata={"source": "admin_test"},
    )
    return create_app_payment(
        app_slug=app.app_slug,
        payload=app_payload,
        request=request,
        db=db,
        x_api_key=app.api_key,
        x_api_secret=app.secret_key,
    )


@router.get("/{app_id}/api-journal")
def app_api_journal(
    app_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application introuvable")
    transactions = (
        db.query(Transaction)
        .filter(Transaction.app_id == app_id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )
    journal = []
    for tx in transactions:
        provider_status_code = None
        if tx.raw_payload:
            try:
                provider_status_code = json.loads(tx.raw_payload).get("provider_status_code")
            except ValueError:
                provider_status_code = None
        journal.append(
            {
                "date": tx.created_at,
                "route": f"/api/v1/apps/{app.app_slug}/payments",
                "status_code": provider_status_code,
                "reference": tx.reference,
                "transaction_id": str(tx.id),
                "phone_masked": _mask_secret(tx.payer_phone, visible=4),
                "amount": tx.amount,
                "currency": tx.currency,
                "telecom": tx.payment_method,
                "result": tx.status,
            }
        )
    return journal


@router.get("/{app_id}/callbacks")
def app_callbacks(
    app_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application introuvable")
    return (
        db.query(WebhookLog)
        .filter(WebhookLog.app_id == app_id)
        .order_by(WebhookLog.created_at.desc())
        .limit(100)
        .all()
    )


@router.get("/companies")
def list_companies(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.VIEWER)),
):
    app_companies = db.query(ConnectedApp.company_id).distinct().all()
    tx_companies = db.query(Transaction.company_id).distinct().all()
    sub_companies = db.query(Subscription.company_id).distinct().all()
    company_ids = sorted({row[0] for row in [*app_companies, *tx_companies, *sub_companies] if row[0]})
    return [
        {
            "company_id": company_id,
            "applications": db.query(func.count(ConnectedApp.id)).filter(ConnectedApp.company_id == company_id).scalar() or 0,
            "transactions": db.query(func.count(Transaction.id)).filter(Transaction.company_id == company_id).scalar() or 0,
            "subscriptions": db.query(func.count(Subscription.id)).filter(Subscription.company_id == company_id).scalar() or 0,
        }
        for company_id in company_ids
    ]


@router.get("/{app_id}/metrics")
def app_metrics(
    app_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    total_transactions = db.query(func.count(Transaction.id)).filter(Transaction.app_id == app_id).scalar() or 0
    total_volume = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(Transaction.app_id == app_id).scalar() or 0.0
    )
    total_commissions = (
        db.query(func.coalesce(func.sum(Transaction.commission), 0.0))
        .filter(Transaction.app_id == app_id)
        .scalar()
        or 0.0
    )
    active_users = (
        db.query(func.count(func.distinct(Transaction.user_id)))
        .filter(Transaction.app_id == app_id, Transaction.status == "success")
        .scalar()
        or 0
    )
    return {
        "app_id": app_id,
        "status": app.status,
        "api_key_active": app.api_key_active,
        "secret_key_active": app.secret_key_active,
        "api_traffic": total_transactions,
        "revenue_by_app": float(total_volume),
        "commissions_by_app": float(total_commissions),
        "active_users": active_users,
    }
