from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)
    app_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    company_id: Mapped[Optional[str]] = mapped_column(String(120), index=True, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
