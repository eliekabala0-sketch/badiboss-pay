from datetime import datetime

from pydantic import BaseModel, Field


class SubscriptionPayRequest(BaseModel):
    company_id: str
    app_id: str
    plan: str = Field(pattern="^(monthly|quarterly|yearly|trial)$")
    amount: float = Field(ge=0)
    start_date: datetime
    end_date: datetime


class SubscriptionResponse(BaseModel):
    id: int
    company_id: str
    app_id: str
    plan: str
    amount: float
    start_date: datetime
    end_date: datetime
    active: bool
    expired: bool
    created_at: datetime

    class Config:
        from_attributes = True
