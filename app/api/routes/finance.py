import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import AdminRole
from app.models.commission import Commission
from app.models.merchant_balance import MerchantBalance
from app.models.merchant_wallet import MerchantWallet
from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.models.withdrawal import Withdrawal

router = APIRouter(prefix="/finance", tags=["Finance"])


@router.get("/wallets")
def list_wallets(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER))):
    return db.query(MerchantWallet).order_by(MerchantWallet.created_at.desc()).limit(300).all()


@router.post("/wallets", status_code=status.HTTP_201_CREATED)
def create_wallet(app_id: str, company_id: str, currency: str = "CDF", db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN))):
    wallet = MerchantWallet(
        app_id=app_id,
        company_id=company_id,
        wallet_reference=f"wl_{uuid.uuid4().hex[:20]}",
        currency=currency,
        status="active",
    )
    db.add(wallet)
    existing_balance = (
        db.query(MerchantBalance)
        .filter(MerchantBalance.app_id == app_id, MerchantBalance.company_id == company_id)
        .first()
    )
    if not existing_balance:
        db.add(MerchantBalance(app_id=app_id, company_id=company_id, available_balance=0.0, pending_balance=0.0, currency=currency))
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/settlements")
def list_settlements(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER))):
    return db.query(Settlement).order_by(Settlement.created_at.desc()).limit(300).all()


@router.post("/settlements", status_code=status.HTTP_201_CREATED)
def create_settlement(app_id: str, company_id: str, amount: float, currency: str = "CDF", db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN))):
    settlement = Settlement(
        app_id=app_id,
        company_id=company_id,
        reference=f"set_{uuid.uuid4().hex[:20]}",
        amount=amount,
        currency=currency,
        status="pending",
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


@router.get("/withdrawals")
def list_withdrawals(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER))):
    return db.query(Withdrawal).order_by(Withdrawal.created_at.desc()).limit(300).all()


@router.post("/withdrawals", status_code=status.HTTP_201_CREATED)
def create_withdrawal(app_id: str, company_id: str, amount: float, currency: str = "CDF", db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN))):
    balance = (
        db.query(MerchantBalance)
        .filter(MerchantBalance.app_id == app_id, MerchantBalance.company_id == company_id)
        .first()
    )
    if not balance:
        raise HTTPException(status_code=404, detail="Merchant balance not found")
    if balance.available_balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient available balance")

    withdrawal = Withdrawal(
        app_id=app_id,
        company_id=company_id,
        reference=f"wd_{uuid.uuid4().hex[:20]}",
        amount=amount,
        currency=currency,
        status="pending",
    )
    balance.available_balance -= amount
    balance.pending_balance += amount
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    return withdrawal


@router.get("/commissions")
def list_commissions(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER))):
    return db.query(Commission).order_by(Commission.created_at.desc()).limit(300).all()


@router.get("/balances")
def list_balances(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER))):
    return db.query(MerchantBalance).order_by(MerchantBalance.updated_at.desc()).limit(300).all()


@router.get("/platform-revenue")
def platform_revenue(
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER)),
):
    total_commissions = db.query(func.coalesce(func.sum(Commission.amount_collected), 0.0)).scalar() or 0.0
    total_provider_fees = db.query(func.coalesce(func.sum(Transaction.fees), 0.0)).scalar() or 0.0
    total_net_platform = float(total_commissions) - float(total_provider_fees)
    return {
        "total_commissions": float(total_commissions),
        "total_provider_fees": float(total_provider_fees),
        "total_net_platform": float(total_net_platform),
    }
