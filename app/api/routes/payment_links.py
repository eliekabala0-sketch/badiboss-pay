from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from urllib.parse import parse_qs

from app.api.deps import get_db, require_roles
from app.core.config import settings
from app.core.roles import AdminRole
from app.models.connected_app import ConnectedApp
from app.models.payment_link import PaymentLink
from app.models.transaction import Transaction
from app.services.serdipay_service import create_payment
from app.services.tracking_service import collect_tracking_data
from app.utils.keys import generate_app_suffix, slugify_app_name

router = APIRouter(tags=["Payment Links"])


class PaymentLinkCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    amount: float = Field(gt=0)
    currency: str
    description: str = ""
    validity: str = "7d"
    custom_expires_at: Optional[datetime] = None
    usage_limit_type: str = "unlimited"
    max_uses: Optional[int] = None
    success_redirect_url: str = ""
    failure_redirect_url: str = ""


def _origin() -> str:
    return f"https://{settings.badiboss_public_domain}"


def _normalize_currency(value: str) -> str:
    currency = str(value or "").upper()
    if currency not in {"USD", "CDF"}:
        raise HTTPException(status_code=400, detail="currency must be USD or CDF")
    return currency


def _expires_at(payload: PaymentLinkCreate) -> datetime | None:
    now = datetime.now(timezone.utc)
    if payload.validity == "24h":
        return now + timedelta(hours=24)
    if payload.validity == "7d":
        return now + timedelta(days=7)
    if payload.validity == "30d":
        return now + timedelta(days=30)
    if payload.validity == "custom":
        return _aware_datetime(payload.custom_expires_at)
    return None


def _aware_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _max_uses(payload: PaymentLinkCreate) -> int | None:
    if payload.usage_limit_type == "single":
        return 1
    if payload.usage_limit_type == "limited":
        return payload.max_uses if payload.max_uses and payload.max_uses > 0 else 1
    return None


def _unique_slug(db: Session, title: str) -> str:
    base_slug = slugify_app_name(title)
    slug = base_slug
    counter = 2
    while db.query(PaymentLink).filter(PaymentLink.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def _payment_link_app(db: Session) -> ConnectedApp:
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == "payment_link").first()
    if app:
        return app
    app = ConnectedApp(
        app_id="payment_link",
        app_slug="payment-link",
        company_id="badiboss-pay",
        api_key=f"internal-payment-link-{generate_app_suffix()}",
        secret_key=f"internal-payment-link-{generate_app_suffix()}",
        webhook_secret=f"internal-payment-link-{generate_app_suffix()}",
        name="Payment links",
        app_type="internal",
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


def _payment_count(db: Session, link_id: int) -> int:
    return db.query(func.count(Transaction.id)).filter(Transaction.payment_link_id == link_id).scalar() or 0


def _link_block_reason(db: Session, link: PaymentLink) -> str | None:
    if not link.is_active or link.status == "inactive":
        return "Lien de paiement desactive."
    expires_at = _aware_datetime(link.expires_at)
    if expires_at and expires_at < datetime.now(timezone.utc):
        return "Lien de paiement expire."
    if link.max_uses is not None and _payment_count(db, link.id) >= link.max_uses:
        return "Nombre d'utilisations atteint."
    return None


def _provider_value(payload: dict, key: str):
    payment = payload.get("payment")
    if isinstance(payment, dict) and payment.get(key) not in (None, ""):
        return payment.get(key)
    return payload.get(key)


def _link_response(db: Session, link: PaymentLink) -> dict:
    totals = {
        "USD": 0.0,
        "CDF": 0.0,
        "success": 0,
        "failed": 0,
        "pending": 0,
    }
    rows = (
        db.query(Transaction.currency, Transaction.status, func.count(Transaction.id), func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(Transaction.payment_link_id == link.id)
        .group_by(Transaction.currency, Transaction.status)
        .all()
    )
    for currency, status, count, amount in rows:
        currency_key = str(currency or "UNKNOWN").upper()
        status_key = str(status or "pending").lower()
        if currency_key in {"USD", "CDF"} and status_key == "success":
            totals[currency_key] += float(amount or 0.0)
        if status_key in {"success", "failed", "pending"}:
            totals[status_key] += int(count or 0)
    return {
        "id": link.id,
        "slug": link.slug,
        "title": link.title,
        "description": link.description or "",
        "amount": link.amount,
        "currency": link.currency,
        "status": "expired" if _aware_datetime(link.expires_at) and _aware_datetime(link.expires_at) < datetime.now(timezone.utc) else link.status,
        "is_active": link.is_active,
        "expires_at": link.expires_at,
        "max_uses": link.max_uses,
        "success_redirect_url": link.success_redirect_url or "",
        "failure_redirect_url": link.failure_redirect_url or "",
        "created_at": link.created_at,
        "public_url": f"{_origin()}/l/{link.slug}",
        "payments_count": _payment_count(db, link.id),
        "total_usd": totals["USD"],
        "total_cdf": totals["CDF"],
        "success_count": totals["success"],
        "failed_count": totals["failed"],
        "pending_count": totals["pending"],
    }


@router.get("/payment-links")
def list_payment_links(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    links = db.query(PaymentLink).order_by(PaymentLink.created_at.desc()).all()
    return [_link_response(db, link) for link in links]


@router.post("/payment-links", status_code=201)
def create_payment_link(
    payload: PaymentLinkCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    link = PaymentLink(
        slug=_unique_slug(db, payload.title),
        title=payload.title,
        description=payload.description or None,
        amount=payload.amount,
        currency=_normalize_currency(payload.currency),
        expires_at=_expires_at(payload),
        max_uses=_max_uses(payload),
        success_redirect_url=payload.success_redirect_url or None,
        failure_redirect_url=payload.failure_redirect_url or None,
        status="active",
        is_active=True,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return _link_response(db, link)


@router.patch("/payment-links/{link_id}/status")
def update_payment_link_status(
    link_id: int,
    active: bool,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    link = db.query(PaymentLink).filter(PaymentLink.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Lien de paiement introuvable")
    link.is_active = active
    link.status = "active" if active else "inactive"
    db.commit()
    db.refresh(link)
    return _link_response(db, link)


@router.get("/payment-links/{link_id}/payments")
def payment_link_payments(
    link_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    rows = (
        db.query(Transaction)
        .filter(Transaction.payment_link_id == link_id)
        .order_by(Transaction.created_at.desc())
        .limit(200)
        .all()
    )
    return rows


@router.get("/l/{slug}", response_class=HTMLResponse)
def public_payment_link(slug: str, db: Session = Depends(get_db)):
    link = db.query(PaymentLink).filter(PaymentLink.slug == slug).first()
    if not link:
        raise HTTPException(status_code=404, detail="Lien de paiement introuvable")
    block_reason = _link_block_reason(db, link)
    escaped_title = html.escape(link.title)
    escaped_description = html.escape(link.description or "")
    disabled = "disabled" if block_reason else ""
    button_label = html.escape(block_reason or "Payer maintenant")
    return f"""
    <!doctype html>
    <html lang="fr">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{escaped_title} - Badiboss Pay</title>
        <style>
          body {{ margin: 0; font-family: Arial, sans-serif; background: #f8fafc; color: #0f172a; }}
          main {{ max-width: 560px; margin: 32px auto; background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; }}
          label {{ display: block; margin-top: 14px; font-size: 14px; font-weight: 600; }}
          input, select {{ width: 100%; box-sizing: border-box; margin-top: 6px; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; }}
          button {{ width: 100%; margin-top: 20px; padding: 12px; border: 0; border-radius: 6px; background: #2563eb; color: white; font-weight: 700; }}
          button:disabled {{ background: #94a3b8; }}
          .brand {{ color: #2563eb; font-weight: 800; }}
          .amount {{ font-size: 28px; font-weight: 800; margin: 8px 0; }}
          .note {{ color: #64748b; }}
        </style>
      </head>
      <body>
        <main>
          <p class="brand">Badiboss Pay</p>
          <h1>{escaped_title}</h1>
          <p class="amount">{link.amount:g} {html.escape(link.currency)}</p>
          <p class="note">{escaped_description}</p>
          <form method="post" action="/l/{html.escape(link.slug)}/pay">
            <label>Nom du payeur<input name="payer_name" required /></label>
            <label>Telephone du payeur<input name="payer_phone" required /></label>
            <label>Telecom
              <select name="telecom">
                <option value="OM">Orange Money</option>
                <option value="AM">Airtel Money</option>
                <option value="MP">M-Pesa</option>
                <option value="Afrimoney">Afrimoney</option>
              </select>
            </label>
            <button type="submit" {disabled}>{button_label}</button>
          </form>
        </main>
      </body>
    </html>
    """


@router.post("/l/{slug}/pay")
async def pay_public_link(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
):
    form_values = parse_qs((await request.body()).decode("utf-8"))
    payer_name = (form_values.get("payer_name") or [""])[0].strip()
    payer_phone = (form_values.get("payer_phone") or [""])[0].strip()
    telecom = (form_values.get("telecom") or ["OM"])[0].strip() or "OM"
    if not payer_name or not payer_phone:
        raise HTTPException(status_code=400, detail="Nom et telephone du payeur requis")
    link = db.query(PaymentLink).filter(PaymentLink.slug == slug).first()
    if not link:
        raise HTTPException(status_code=404, detail="Lien de paiement introuvable")
    block_reason = _link_block_reason(db, link)
    if block_reason:
        raise HTTPException(status_code=403, detail=block_reason)

    payment_app = _payment_link_app(db)
    reference = f"LINK-{link.slug[:24]}-{generate_app_suffix()}".upper()
    tracking = collect_tracking_data(request, source_application="payment_link")
    tx = Transaction(
        reference=reference,
        app_id=payment_app.app_id,
        payment_link_id=link.id,
        user_id=payer_phone,
        customer_name=payer_name,
        payer_phone=payer_phone,
        company_id=payment_app.company_id,
        amount=link.amount,
        currency=link.currency,
        status="pending",
        provider="serdipay",
        raw_payload=json.dumps({"payment_link_id": link.id, "title": link.title}, ensure_ascii=True),
        fees=0.0,
        commission=0.0,
        net_amount=link.amount,
        payment_method=telecom,
        public_ip=tracking["public_ip"],
        country=tracking["country"],
        city=tracking["city"],
        region=tracking["region"],
        isp=tracking["isp"],
        device=tracking["device"],
        browser=tracking["browser"],
        operating_system=tracking["operating_system"],
        device_type=tracking["device_type"],
        source_application=f"Paiement par lien: {link.title}",
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)

    provider_payload = create_payment(phone=payer_phone, amount=link.amount, currency=link.currency, telecom=telecom)
    provider_response = provider_payload.get("serdipay_response", {})
    if not isinstance(provider_response, dict):
        provider_response = {"raw_response": provider_response}
    provider_status_code = provider_payload.get("serdipay_status_code", 500)
    tx.provider_reference = str(_provider_value(provider_response, "transactionId") or "") or None
    provider_session_id = _provider_value(provider_response, "sessionId")
    tx.provider_session_id = str(provider_session_id) if provider_session_id not in (None, "") else None
    tx.raw_payload = json.dumps(
        {"provider_status_code": provider_status_code, "provider_response": provider_response},
        ensure_ascii=True,
    )
    if provider_status_code >= 400 and provider_response.get("message") == "SerdiPay token unavailable":
        tx.status = "failed"
    db.commit()

    if tx.status == "success" and link.success_redirect_url:
        return RedirectResponse(link.success_redirect_url, status_code=303)
    if tx.status == "failed" and link.failure_redirect_url:
        return RedirectResponse(link.failure_redirect_url, status_code=303)
    message = "Paiement recu avec succes. Merci." if tx.status == "success" else "Paiement envoye. Statut en attente de confirmation."
    if tx.status == "failed":
        message = "Paiement echoue. Veuillez reessayer."
    return HTMLResponse(f"<main style='font-family:Arial;padding:32px'><h1>Badiboss Pay</h1><p>{html.escape(message)}</p><p>Reference: {html.escape(tx.reference)}</p></main>")
