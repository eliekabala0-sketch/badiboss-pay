from sqlalchemy import case, func
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.transaction import Transaction

router = APIRouter(tags=["Analytics"])


def _phone_brand(device_value: Optional[str]) -> str:
    if not device_value:
        return "unknown"
    lowered = device_value.lower()
    for brand in ("samsung", "huawei", "xiaomi", "iphone", "tecno", "infinix", "nokia"):
        if brand in lowered:
            return brand
    return "unknown"


@router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    by_city = (
        db.query(
            Transaction.city,
            func.count(Transaction.id).label("transactions"),
        )
        .group_by(Transaction.city)
        .order_by(func.count(Transaction.id).desc())
        .limit(20)
        .all()
    )
    by_device_type = (
        db.query(
            Transaction.device_type,
            func.count(Transaction.id).label("transactions"),
        )
        .group_by(Transaction.device_type)
        .order_by(func.count(Transaction.id).desc())
        .all()
    )
    by_platform = (
        db.query(
            case(
                (Transaction.operating_system.ilike("%android%"), "Android"),
                (Transaction.operating_system.ilike("%iphone%"), "iPhone"),
                (Transaction.operating_system.ilike("%ios%"), "iPhone"),
                else_="Desktop",
            ).label("platform"),
            func.count(Transaction.id).label("transactions"),
        )
        .group_by("platform")
        .order_by(func.count(Transaction.id).desc())
        .all()
    )
    recent_users = (
        db.query(
            Transaction.app_id,
            Transaction.user_id,
            Transaction.public_ip,
            Transaction.country,
            Transaction.city,
            Transaction.device,
            Transaction.operating_system,
            Transaction.browser,
            Transaction.source_application,
            Transaction.created_at,
        )
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )

    by_app = (
        db.query(
            Transaction.app_id,
            func.count(Transaction.id).label("transactions"),
            func.coalesce(func.sum(Transaction.amount), 0.0).label("volume"),
        )
        .group_by(Transaction.app_id)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )
    by_country = (
        db.query(
            Transaction.country,
            func.count(Transaction.id).label("transactions"),
        )
        .group_by(Transaction.country)
        .order_by(func.count(Transaction.id).desc())
        .all()
    )
    return {
        "transactions_by_app": [
            {"app_id": row.app_id, "transactions": row.transactions, "volume": float(row.volume or 0.0)}
            for row in by_app
        ],
        "transactions_by_country": [
            {"country": row.country or "unknown", "transactions": row.transactions} for row in by_country
        ],
        "transactions_by_city": [{"city": row.city or "unknown", "transactions": row.transactions} for row in by_city],
        "users_by_application": [
            {"app_id": row.app_id, "transactions": row.transactions, "volume": float(row.volume or 0.0)}
            for row in by_app
        ],
        "device_types": [
            {"device_type": row.device_type or "unknown", "transactions": row.transactions}
            for row in by_device_type
        ],
        "platforms": [{"platform": row.platform, "transactions": row.transactions} for row in by_platform],
        "recent_activity": [
            {
                "app_id": row.app_id,
                "user_id": row.user_id,
                "ip": row.public_ip,
                "country": row.country,
                "city": row.city,
                "device": row.device,
                "phone_brand": _phone_brand(row.device),
                "os": row.operating_system,
                "browser": row.browser,
                "source_application": row.source_application,
                "created_at": row.created_at,
            }
            for row in recent_users
        ],
    }
