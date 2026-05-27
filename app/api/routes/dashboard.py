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
    total_collected = db.query(func.coalesce(func.sum(Transaction.amount), 0.0)).filter(Transaction.status == "success").scalar() or 0.0
    total_provider_fees = db.query(func.coalesce(func.sum(Transaction.fees), 0.0)).filter(Transaction.status == "success").scalar() or 0.0
    total_commissions = db.query(func.coalesce(func.sum(Transaction.commission), 0.0)).scalar() or 0.0
    merchant_net = db.query(func.coalesce(func.sum(Transaction.net_amount), 0.0)).filter(Transaction.status == "success").scalar() or 0.0
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
    merchant_available_balance = db.query(func.coalesce(func.sum(MerchantBalance.available_balance), 0.0)).scalar() or 0.0
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
