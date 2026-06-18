import csv
import io
from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.transaction import Transaction
router = APIRouter(tags=["Transactions"])


@router.get("/transactions")
def list_transactions(
    app_id: Optional[str] = Query(default=None),
    company_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    currency: Optional[str] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    phone: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    query = db.query(Transaction)
    if app_id:
        query = query.filter(Transaction.app_id == app_id)
    if company_id:
        query = query.filter(Transaction.company_id == company_id)
    if status:
        query = query.filter(Transaction.status == status)
    if currency:
        query = query.filter(Transaction.currency == currency.upper())
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    if phone:
        query = query.filter(Transaction.payer_phone == phone)
    if search:
        like_value = f"%{search}%"
        query = query.filter(
            (Transaction.reference.ilike(like_value))
            | (Transaction.user_id.ilike(like_value))
            | (Transaction.payer_phone.ilike(like_value))
            | (Transaction.app_id.ilike(like_value))
            | (Transaction.company_id.ilike(like_value))
            | (Transaction.provider_reference.ilike(like_value))
            | (Transaction.provider_session_id.ilike(like_value))
        )
    if date_from:
        query = query.filter(Transaction.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        query = query.filter(Transaction.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))

    total = query.count()
    items = (
        query.order_by(Transaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/transactions/export")
def export_transactions_csv(
    app_id: Optional[str] = Query(default=None),
    company_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    currency: Optional[str] = Query(default=None),
    phone: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN)),
):
    query = db.query(Transaction)
    if app_id:
        query = query.filter(Transaction.app_id == app_id)
    if company_id:
        query = query.filter(Transaction.company_id == company_id)
    if status:
        query = query.filter(Transaction.status == status)
    if currency:
        query = query.filter(Transaction.currency == currency.upper())
    if phone:
        query = query.filter(Transaction.payer_phone == phone)
    if search:
        like_value = f"%{search}%"
        query = query.filter(
            (Transaction.reference.ilike(like_value))
            | (Transaction.user_id.ilike(like_value))
            | (Transaction.payer_phone.ilike(like_value))
            | (Transaction.app_id.ilike(like_value))
            | (Transaction.company_id.ilike(like_value))
            | (Transaction.provider_reference.ilike(like_value))
            | (Transaction.provider_session_id.ilike(like_value))
        )
    if date_from:
        query = query.filter(Transaction.created_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        query = query.filter(Transaction.created_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
    rows = query.order_by(Transaction.created_at.desc()).limit(5000).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "reference",
            "app_id",
            "company_id",
            "user_id",
            "payer_phone",
            "amount",
            "amount_display",
            "currency",
            "status",
            "provider",
            "provider_reference",
            "provider_session_id",
            "fees",
            "commission",
            "net_amount",
            "public_ip",
            "country",
            "city",
            "device",
            "operating_system",
            "browser",
            "source_application",
            "created_at",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.reference,
                row.app_id,
                row.company_id,
                row.user_id,
                row.payer_phone or "",
                row.amount,
                "N/A" if row.payment_method == "callback_test" else row.amount,
                row.currency,
                row.status,
                row.provider,
                row.provider_reference or "",
                row.provider_session_id or "",
                row.fees,
                row.commission,
                row.net_amount,
                row.public_ip or "",
                row.country or "",
                row.city or "",
                row.device or "",
                row.operating_system or "",
                row.browser or "",
                row.source_application or "",
                row.created_at.isoformat(),
            ]
        )
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions_export.csv"'},
    )
