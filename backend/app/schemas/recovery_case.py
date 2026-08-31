from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.customer import CustomerResponse
from app.schemas.event import PaymentEventResponse


class RecoveryActionResponse(BaseModel):
    id: int
    recovery_case_id: int
    action_type: str
    status: str
    external_reference: Optional[str] = None
    payment_link_id: Optional[str] = None
    payment_link_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RecoveryCaseListItem(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    amount: int  # in paise
    currency: str = "INR"
    event_type: str
    failure_reason: Optional[str] = None
    risk_score: float  # 0 to 100
    recovery_probability: float  # 0.0 to 1.0
    recommended_action: str
    confidence: float  # 0.0 to 1.0
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecoveryCaseDetailResponse(BaseModel):
    id: int
    customer_id: int
    payment_event_id: int
    risk_score: float
    recovery_probability: float
    recommended_action: str
    confidence: float
    status: str
    created_at: datetime
    customer: CustomerResponse
    payment_event: PaymentEventResponse
    recovery_actions: List[RecoveryActionResponse] = []
    scoring_breakdown: Optional[dict] = None

    class Config:
        from_attributes = True
