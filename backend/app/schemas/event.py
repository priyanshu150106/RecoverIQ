from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.customer import CustomerResponse


class RawEventPayload(BaseModel):
    event_type: str = Field(..., description="Event type name (e.g. payment.failed, payment_link.expired)")
    customer: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Customer information dictionary")
    amount: int = Field(..., description="Transaction amount in paise (1 INR = 100 paise)")
    currency: str = Field(default="INR", description="Currency code")
    status: Optional[str] = Field(None, description="Event status")
    failure_reason: Optional[str] = Field(None, description="Detailed failure or expiry reason")
    external_event_id: Optional[str] = Field(None, description="Unique external event identifier")
    created_at: Optional[datetime] = Field(None, description="Original event timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary raw metadata")


class NormalizedCustomerInfo(BaseModel):
    name: str = "Unknown Customer"
    email: str
    phone: Optional[str] = None


class NormalizedEvent(BaseModel):
    event_type: str
    customer: NormalizedCustomerInfo
    amount: int  # in paise
    currency: str = "INR"
    status: str
    failure_reason: Optional[str] = None
    external_event_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PaymentEventResponse(BaseModel):
    id: int
    customer_id: int
    event_type: str
    amount: int  # in paise
    currency: str
    status: str
    failure_reason: Optional[str] = None
    external_event_id: Optional[str] = None
    created_at: datetime
    customer: Optional[CustomerResponse] = None

    class Config:
        from_attributes = True


class EventIngestionResponse(BaseModel):
    status: str
    message: str
    is_duplicate: bool = False
    payment_event: PaymentEventResponse
    recovery_case_id: Optional[int] = None
