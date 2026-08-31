from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ExecuteLinkRequest(BaseModel):
    description: Optional[str] = Field(None, description="Custom payment link description")
    expire_hours: Optional[int] = Field(24, ge=1, le=720, description="Link expiry window in hours (default 24h)")


class ExecuteLinkResponse(BaseModel):
    status: str = Field(..., description="Execution status ('success' or 'error')")
    message: str
    recovery_case_id: int
    action_id: int
    payment_link_id: str
    payment_link_url: str
    amount: int  # in paise
    currency: str = "INR"
    status_code: int = 200


class PolicyCheckResult(BaseModel):
    allowed: bool
    policy_name: str
    reason: Optional[str] = None
