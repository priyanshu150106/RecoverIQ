from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


ActorType = Literal[
    "AI_AGENT",
    "POLICY_ENGINE",
    "RAZORPAY_EXECUTION",
    "WEBHOOK_RECEIVER",
    "SYSTEM",
]

ActionType = Literal[
    "FAILURE_DETECTED",
    "AI_DIAGNOSED",
    "POLICY_PASSED",
    "LINK_GENERATED",
    "PAYMENT_CAPTURED",
    "PAYMENT_PARTIALLY_CAPTURED",
    "PAYMENT_CANCELLED",
    "PAYMENT_EXPIRED",
    "CASE_RECOVERED",
    "RECOVERY_ACTION_FAILED",
]


class ActivityItem(BaseModel):
    id: str = Field(..., description="Unique activity event identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of the activity")
    actor: ActorType = Field(..., description="System entity that initiated or produced this event")
    action: ActionType = Field(..., description="Standardized lifecycle action code")
    summary: str = Field(..., description="Human-readable operational summary")
    status: str = Field(..., description="Status string of the underlying record")
    case_id: Optional[int] = Field(None, description="Associated RecoveryCase ID when available")
    amount: Optional[int] = Field(None, description="Transaction amount in paise when applicable")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Sanitized contextual metadata")

    class Config:
        from_attributes = True
