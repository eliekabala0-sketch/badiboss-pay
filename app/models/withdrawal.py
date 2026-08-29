from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    reference: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="CDF", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    destination_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    mobile_operator: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    mobile_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    account_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    bank_swift: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    provider_reference: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    requested_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
