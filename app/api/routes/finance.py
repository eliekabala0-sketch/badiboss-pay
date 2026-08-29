import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
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
from app.utils.phone import normalize_drc_phone

router = APIRouter(prefix="/finance", tags=["Finance"])
CURRENCIES = ("USD", "CDF")


class WithdrawalCreate(BaseModel):
    app_id: str = Field(min_length=1, max_length=64)
    company_id: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0)
    currency: str = "CDF"
    destination_type: Literal["mobile_money", "bank_account"]
    mobile_operator: Optional[Literal["OM", "AM", "MP", "AF"]] = None
    mobile_phone: Optional[str] = None
    bank_name: Optional[str] = Field(default=None, max_length=160)
    account_name: Optional[str] = Field(default=None, max_length=160)
    account_number: Optional[str] = Field(default=None, max_length=120)
    bank_swift: Optional[str] = Field(default=None, max_length=40)
    requested_by: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_destination(self):
        if self.destination_type == "mobile_money":
            if not self.mobile_operator or not self.mobile_phone:
                raise ValueError("Operateur et numero Mobile Money requis")
            self.mobile_phone = normalize_drc_phone(self.mobile_phone)
        else:
            if not self.bank_name or not self.account_name or not self.account_number:
                raise ValueError("Banque, titulaire et numero de compte requis")
        return self


class WithdrawalStatusUpdate(BaseModel):
    status: Literal["processing", "completed", "failed", "cancelled"]
    provider_reference: Optional[str] = Field(default=None, max_length=160)
    failure_reason: Optional[str] = Field(default=None, max_length=500)
    approved_by: Optional[str] = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_result(self):
        if self.status == "completed" and not self.provider_reference:
            raise ValueError("La reference SerdiPay ou bancaire est requise pour confirmer le reversement")
        if self.status == "failed" and not self.failure_reason:
            raise ValueError("Le motif de l'echec est requis")
        return self


def _normalize_currency(currency: str) -> str:
    normalized = str(currency or "CDF").upper()
    return normalized if normalized in CURRENCIES else "CDF"


def _transaction_sum_by_currency(db: Session, column) -> dict[str, float]:
    rows = (
        db.query(Transaction.currency, func.coalesce(func.sum(column), 0.0))
        .filter(Transaction.status == "success")
        .group_by(Transaction.currency)
        .all()
    )
    totals = {currency: 0.0 for currency in CURRENCIES}
    for currency, value in rows:
        totals[_normalize_currency(currency)] = float(value or 0.0)
    return totals


@router.get("/wallets")
def list_wallets(db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN, AdminRole.VIEWER))):
    return db.query(MerchantWallet).order_by(MerchantWallet.created_at.desc()).limit(300).all()


@router.post("/wallets", status_code=status.HTTP_201_CREATED)
def create_wallet(app_id: str, company_id: str, currency: str = "CDF", db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN))):
    currency = _normalize_currency(currency)
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
        .filter(MerchantBalance.app_id == app_id, MerchantBalance.company_id == company_id, MerchantBalance.currency == currency)
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
    currency = _normalize_currency(currency)
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
def create_withdrawal(payload: WithdrawalCreate, db: Session = Depends(get_db), _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN))):
    currency = _normalize_currency(payload.currency)
    balance = (
        db.query(MerchantBalance)
        .filter(
            MerchantBalance.app_id == payload.app_id,
            MerchantBalance.company_id == payload.company_id,
            MerchantBalance.currency == currency,
        )
        .with_for_update()
        .first()
    )
    if not balance:
        raise HTTPException(status_code=404, detail="Merchant balance not found")
    if balance.available_balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient available balance")

    withdrawal = Withdrawal(
        app_id=payload.app_id,
        company_id=payload.company_id,
        reference=f"wd_{uuid.uuid4().hex[:20]}",
        amount=payload.amount,
        currency=currency,
        status="pending",
        destination_type=payload.destination_type,
        mobile_operator=payload.mobile_operator,
        mobile_phone=payload.mobile_phone,
        bank_name=payload.bank_name,
        account_name=payload.account_name,
        account_number=payload.account_number,
        bank_swift=payload.bank_swift,
        requested_by=payload.requested_by,
    )
    balance.available_balance -= payload.amount
    balance.pending_balance += payload.amount
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    return withdrawal


@router.patch("/withdrawals/{withdrawal_id}")
def update_withdrawal_status(
    withdrawal_id: int,
    payload: WithdrawalStatusUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(AdminRole.SUPER_ADMIN, AdminRole.FINANCE_ADMIN)),
):
    withdrawal = db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id).with_for_update().first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    allowed = {
        "pending": {"processing", "completed", "failed", "cancelled"},
        "processing": {"completed", "failed", "cancelled"},
    }
    if payload.status not in allowed.get(withdrawal.status, set()):
        raise HTTPException(status_code=409, detail=f"Invalid withdrawal transition: {withdrawal.status} -> {payload.status}")

    balance = (
        db.query(MerchantBalance)
        .filter(
            MerchantBalance.app_id == withdrawal.app_id,
            MerchantBalance.company_id == withdrawal.company_id,
            MerchantBalance.currency == withdrawal.currency,
        )
        .with_for_update()
        .first()
    )
    if not balance:
        raise HTTPException(status_code=404, detail="Merchant balance not found")

    withdrawal.status = payload.status
    withdrawal.provider_reference = payload.provider_reference
    withdrawal.failure_reason = payload.failure_reason
    withdrawal.approved_by = payload.approved_by
    if payload.status in {"completed", "failed", "cancelled"}:
        if balance.pending_balance < withdrawal.amount:
            raise HTTPException(status_code=409, detail="Reserved withdrawal balance is inconsistent")
        balance.pending_balance -= withdrawal.amount
        withdrawal.processed_at = datetime.now(timezone.utc)
        if payload.status in {"failed", "cancelled"}:
            balance.available_balance += withdrawal.amount
        db.add(
            Settlement(
                app_id=withdrawal.app_id,
                company_id=withdrawal.company_id,
                reference=f"set_{uuid.uuid4().hex[:20]}",
                amount=withdrawal.amount,
                currency=withdrawal.currency,
                status="completed" if payload.status == "completed" else "failed",
                withdrawal_reference=withdrawal.reference,
                destination_type=withdrawal.destination_type,
                provider_reference=payload.provider_reference,
                processed_at=withdrawal.processed_at,
            )
        )

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
    commission_rows = (
        db.query(Transaction.currency, func.coalesce(func.sum(Transaction.commission), 0.0))
        .filter(Transaction.status == "success")
        .group_by(Transaction.currency)
        .all()
    )
    commissions_by_currency = {currency: 0.0 for currency in CURRENCIES}
    for currency, value in commission_rows:
        commissions_by_currency[_normalize_currency(currency)] = float(value or 0.0)
    provider_fees_by_currency = _transaction_sum_by_currency(db, Transaction.fees)
    net_by_currency = {
        currency: commissions_by_currency[currency] - provider_fees_by_currency[currency]
        for currency in CURRENCIES
    }
    total_commissions = sum(commissions_by_currency.values())
    total_provider_fees = sum(provider_fees_by_currency.values())
    total_net_platform = sum(net_by_currency.values())
    return {
        "total_commissions": float(total_commissions),
        "total_provider_fees": float(total_provider_fees),
        "total_net_platform": float(total_net_platform),
        "by_currency": {
            currency: {
                "total_commissions": commissions_by_currency[currency],
                "total_provider_fees": provider_fees_by_currency[currency],
                "total_net_platform": net_by_currency[currency],
            }
            for currency in CURRENCIES
        },
    }
