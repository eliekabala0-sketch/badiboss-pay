from datetime import datetime

from pydantic import BaseModel, Field


class ConnectedAppCreate(BaseModel):
    app_id: str = Field(min_length=3, max_length=64)
    company_id: str = Field(min_length=2, max_length=120)
    name: str
    app_type: str
    callback_url: str
    status: str = "active"
    commission_type: str = "percentage"
    commission_value: float = 0.0


class ConnectedAppResponse(BaseModel):
    id: int
    app_id: str
    company_id: str
    api_key: str
    secret_key: str
    name: str
    app_type: str
    callback_url: str
    status: str
    api_key_active: bool
    secret_key_active: bool
    commission_type: str
    commission_value: float
    created_at: datetime

    class Config:
        from_attributes = True
