from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reference: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    app_id: Mapped[str] = mapped_column(String(64), ForeignKey("connected_apps.app_id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(120), nullable=False)
    payer_phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    company_id: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="UNKNOWN", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="serdipay", nullable=False)
    provider_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    provider_session_id: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    raw_payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fees: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    commission: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    net_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    public_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    isp: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    browser: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    operating_system: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    device_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    source_application: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    app = relationship("ConnectedApp", back_populates="transactions")
