from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    app_id: str
    api_key: str
    secret_key: str
    user_id: str
    company_id: str
    phone: str
    amount: float = Field(gt=0)
    currency: str
    telecom: str = "AM"
    payment_method: str = "mobile_money"
    source_application: Optional[str] = None


class PaymentStatusRequest(BaseModel):
    reference: str


class AppPaymentRequest(BaseModel):
    reference: str = Field(min_length=2, max_length=80)
    customer_id: str = Field(min_length=1, max_length=120)
    customer_name: Optional[str] = None
    clientPhone: str = Field(min_length=8, max_length=40)
    amount: float = Field(gt=0)
    currency: str
    telecom: str = "AM"
    description: Optional[str] = None
    callback_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransactionResponse(BaseModel):
    id: int
    reference: str
    app_id: str
    user_id: str
    customer_name: Optional[str]
    payer_phone: Optional[str]
    company_id: str
    amount: float
    currency: str
    status: str
    provider: str
    provider_reference: Optional[str]
    provider_session_id: Optional[str]
    callback_url: Optional[str]
    metadata_json: Optional[str]
    fees: float
    commission: float
    net_amount: float
    payment_method: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
