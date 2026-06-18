from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    app_id: str
    api_key: str
    secret_key: str
    user_id: str
    company_id: str
    phone: str
    amount: float = Field(gt=0)
    currency: str = "CDF"
    telecom: str = "AM"
    payment_method: str = "mobile_money"
    source_application: Optional[str] = None


class PaymentStatusRequest(BaseModel):
    reference: str


class TransactionResponse(BaseModel):
    id: int
    reference: str
    app_id: str
    user_id: str
    payer_phone: Optional[str]
    company_id: str
    amount: float
    currency: str
    status: str
    provider: str
    provider_reference: Optional[str]
    provider_session_id: Optional[str]
    fees: float
    commission: float
    net_amount: float
    payment_method: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
