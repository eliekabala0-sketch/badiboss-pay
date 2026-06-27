from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConnectedApp(Base):
    __tablename__ = "connected_apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    app_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    app_slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    api_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    secret_key: Mapped[str] = mapped_column(String(128), nullable=False)
    webhook_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    app_type: Mapped[str] = mapped_column(String(100), nullable=False)
    callback_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    api_key_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    secret_key_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    commission_type: Mapped[str] = mapped_column(String(20), default="percentage", nullable=False)
    commission_value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    transactions = relationship("Transaction", back_populates="app")
    subscriptions = relationship("Subscription", back_populates="app")
