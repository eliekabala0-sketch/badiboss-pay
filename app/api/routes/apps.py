from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.connected_app import ConnectedApp
from app.models.transaction import Transaction
from app.schemas.apps import ConnectedAppCreate, ConnectedAppResponse, ConnectedAppUpdate
from app.models.subscription import Subscription
from app.utils.keys import generate_api_key, generate_secret_key

router = APIRouter(prefix="/apps", tags=["Connected Apps"])


@router.get("", response_model=list[ConnectedAppResponse])
def list_apps(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.VIEWER))):
    return db.query(ConnectedApp).order_by(ConnectedApp.created_at.desc()).all()


@router.post("/create", response_model=ConnectedAppResponse, status_code=status.HTTP_201_CREATED)
def create_app(
    payload: ConnectedAppCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.SUPPORT_ADMIN)),
):
    app_id = payload.app_id.strip() or f"bbp_app_{generate_api_key().split('_')[-1][:12]}"
    exists = db.query(ConnectedApp).filter(ConnectedApp.app_id == app_id).first()
    if exists:
        raise HTTPException(status_code=400, detail="Cet identifiant d'application existe deja")

    app = ConnectedApp(
        app_id=app_id,
        company_id=payload.company_id,
        api_key=generate_api_key(),
        secret_key=generate_secret_key(),
        name=payload.name,
        app_type=payload.app_type,
        callback_url=payload.callback_url,
        status=payload.status,
        commission_type=payload.commission_type,
        commission_value=payload.commission_value,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


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
    db.commit()
    db.refresh(app)
    return app


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
    return app


@router.patch("/{app_id}/keys")
def toggle_app_keys(
    app_id: str,
    api_key_active: Optional[bool] = None,
    secret_key_active: Optional[bool] = None,
    regenerate: bool = False,
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
    if regenerate:
        app.api_key = generate_api_key()
        app.secret_key = generate_secret_key()
        app.api_key_active = True
        app.secret_key_active = True
    db.commit()
    db.refresh(app)
    return app


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
