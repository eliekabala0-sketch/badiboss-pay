from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.connected_app import ConnectedApp
from app.models.subscription import Subscription
from app.schemas.subscriptions import SubscriptionPayRequest, SubscriptionResponse

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("/pay", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def pay_subscription(
    payload: SubscriptionPayRequest,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN)),
):
    app = db.query(ConnectedApp).filter(ConnectedApp.app_id == payload.app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    subscription = Subscription(
        company_id=payload.company_id,
        app_id=payload.app_id,
        plan=payload.plan,
        amount=payload.amount,
        start_date=payload.start_date,
        end_date=payload.end_date,
        active=True,
        expired=False,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


@router.get("", response_model=list[SubscriptionResponse])
def list_subscriptions(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    return db.query(Subscription).order_by(Subscription.created_at.desc()).limit(300).all()
