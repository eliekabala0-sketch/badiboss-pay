from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field


class ConnectedAppCreate(BaseModel):
    company_id: str = Field(min_length=2, max_length=120)
    name: str
    app_type: str
    callback_url: str = ""
    status: str = "active"
    commission_type: str = "percentage"
    commission_value: float = 0.0


class ConnectedAppUpdate(BaseModel):
    company_id: Optional[str] = Field(default=None, min_length=2, max_length=120)
    name: Optional[str] = None
    app_type: Optional[str] = None
    callback_url: Optional[str] = None
    status: Optional[str] = None
    commission_type: Optional[str] = None
    commission_value: Optional[float] = None


class ConnectedAppResponse(BaseModel):
    id: int
    app_id: str
    app_slug: str
    company_id: str
    api_key: str
    secret_key: str
    webhook_secret: str
    name: str
    app_type: str
    callback_url: str
    status: str
    api_key_active: bool
    secret_key_active: bool
    commission_type: str
    commission_value: float
    created_at: datetime
    payment_url: str
    status_url: str
    callback_badiboss_pay: str
    transactions_count: int = 0
    total_usd: float = 0.0
    total_cdf: float = 0.0
    success_count: int = 0
    failed_count: int = 0
    pending_count: int = 0
    api_secret_once: Optional[str] = None
    webhook_secret_once: Optional[str] = None

    class Config:
        from_attributes = True
