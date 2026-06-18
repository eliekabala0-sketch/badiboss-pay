from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.api_log import ApiLog
from app.models.connected_app import ConnectedApp
from app.models.merchant_balance import MerchantBalance
from app.models.merchant_wallet import MerchantWallet
from app.models.settlement import Settlement
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.webhook_log import WebhookLog
from app.models.withdrawal import Withdrawal

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

CURRENCIES = ("USD", "CDF")


def _sum_by_currency(db: Session, model, amount_column, *filters) -> dict[str, float]:
    rows = (
        db.query(model.currency, func.coalesce(func.sum(amount_column), 0.0))
        .filter(*filters)
        .group_by(model.currency)
        .all()
    )
    totals = {currency: 0.0 for currency in CURRENCIES}
    for currency, value in rows:
        currency_key = str(currency or "CDF").upper()
        totals[currency_key] = float(value or 0.0)
    return totals


def _count_transactions_by_currency(db: Session, *filters) -> dict[str, int]:
    rows = (
        db.query(Transaction.currency, func.count(Transaction.id))
        .filter(*filters)
        .group_by(Transaction.currency)
        .all()
    )
    totals = {currency: 0 for currency in CURRENCIES}
    for currency, value in rows:
        currency_key = str(currency or "CDF").upper()
        totals[currency_key] = int(value or 0)
    return totals


def _status_counts(db: Session) -> dict[str, int]:
    rows = db.query(Transaction.status, func.count(Transaction.id)).group_by(Transaction.status).all()
    counts = {"success": 0, "failed": 0, "pending": 0}
    for status, value in rows:
        status_key = str(status or "pending").lower()
        if status_key in {"cancelled", "canceled", "error"}:
            status_key = "failed"
        if status_key not in counts:
            status_key = "pending"
        counts[status_key] += int(value or 0)
    return counts


def _currency_breakdown(db: Session, start_today: datetime, start_month: datetime) -> dict[str, dict[str, float | int]]:
    collected = _sum_by_currency(db, Transaction, Transaction.amount, Transaction.status == "success")
    provider_fees = _sum_by_currency(db, Transaction, Transaction.fees, Transaction.status == "success")
    commissions = _sum_by_currency(db, Transaction, Transaction.commission, Transaction.status == "success")
    merchant_net = _sum_by_currency(db, Transaction, Transaction.net_amount, Transaction.status == "success")
    balances = _sum_by_currency(db, MerchantBalance, MerchantBalance.available_balance)
    revenue_today = _sum_by_currency(
        db,
        Transaction,
        Transaction.commission,
        Transaction.status == "success",
        Transaction.created_at >= start_today,
    )
    revenue_month = _sum_by_currency(
        db,
        Transaction,
        Transaction.commission,
        Transaction.status == "success",
        Transaction.created_at >= start_month,
    )
    transaction_counts = _count_transactions_by_currency(db)
    success_counts = _count_transactions_by_currency(db, Transaction.status == "success")
    failed_counts = _count_transactions_by_currency(db, Transaction.status.in_(["failed", "cancelled", "canceled", "error"]))
    pending_counts = _count_transactions_by_currency(db, Transaction.status == "pending")

    return {
        currency: {
            "total_collected": collected[currency],
            "total_provider_fees": provider_fees[currency],
            "total_commissions": commissions[currency],
            "merchant_net": merchant_net[currency],
            "merchant_available_balance": balances[currency],
            "revenue_today": revenue_today[currency],
            "revenue_month": revenue_month[currency],
            "total_transactions": transaction_counts[currency],
            "success": success_counts[currency],
            "failed": failed_counts[currency],
            "pending": pending_counts[currency],
        }
        for currency in CURRENCIES
    }


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    now = datetime.now(timezone.utc)
    start_today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    start_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    total_apps = db.query(func.count(ConnectedApp.id)).scalar() or 0
    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
    by_currency = _currency_breakdown(db, start_today, start_month)
    total_collected = sum(currency_data["total_collected"] for currency_data in by_currency.values())
    total_provider_fees = sum(currency_data["total_provider_fees"] for currency_data in by_currency.values())
    total_commissions = sum(currency_data["total_commissions"] for currency_data in by_currency.values())
    merchant_net = sum(currency_data["merchant_net"] for currency_data in by_currency.values())
    revenue_today = (
        db.query(func.coalesce(func.sum(Transaction.commission), 0.0))
        .filter(and_(Transaction.created_at >= start_today, Transaction.status == "success"))
        .scalar()
        or 0.0
    )
    revenue_month = (
        db.query(func.coalesce(func.sum(Transaction.commission), 0.0))
        .filter(and_(Transaction.created_at >= start_month, Transaction.status == "success"))
        .scalar()
        or 0.0
    )
    active_subscriptions = db.query(func.count(Subscription.id)).filter(Subscription.active.is_(True)).scalar() or 0
    wallets = db.query(func.count(MerchantWallet.id)).scalar() or 0
    settlements_pending = (
        db.query(func.count(Settlement.id)).filter(Settlement.status == "pending").scalar() or 0
    )
    settlements_done = db.query(func.count(Settlement.id)).filter(Settlement.status.in_(["paid", "completed", "success"])).scalar() or 0
    settlement_errors = db.query(func.count(Settlement.id)).filter(Settlement.status.in_(["failed", "error"])).scalar() or 0
    withdrawals_count = db.query(func.count(Withdrawal.id)).scalar() or 0
    withdrawals_pending = db.query(func.count(Withdrawal.id)).filter(Withdrawal.status == "pending").scalar() or 0
    merchant_available_balance = sum(currency_data["merchant_available_balance"] for currency_data in by_currency.values())
    api_errors = db.query(func.count(ApiLog.id)).filter(ApiLog.status_code >= 400).scalar() or 0
    webhook_errors = (
        db.query(func.count(WebhookLog.id))
        .filter((WebhookLog.status_code >= 400) | (WebhookLog.error_message.isnot(None)))
        .scalar()
        or 0
    )

    recent_window = now - timedelta(minutes=30)
    realtime_activity = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.created_at >= recent_window)
        .scalar()
        or 0
    )

    return {
        "total_apps": total_apps,
        "total_transactions": total_transactions,
        "total_collected": float(total_collected),
        "total_provider_fees": float(total_provider_fees),
        "total_commissions": float(total_commissions),
        "merchant_net": float(merchant_net),
        "merchant_available_balance": float(merchant_available_balance),
        "by_currency": by_currency,
        "status_counts": _status_counts(db),
        "revenue_today": float(revenue_today),
        "revenue_month": float(revenue_month),
        "active_subscriptions": active_subscriptions,
        "wallets_merchants": wallets,
        "settlements_pending": settlements_pending,
        "settlements_done": settlements_done,
        "settlement_errors": settlement_errors,
        "withdrawals": withdrawals_count,
        "withdrawals_pending": withdrawals_pending,
        "api_webhook_errors": api_errors + webhook_errors,
        "realtime_activity": realtime_activity,
    }
