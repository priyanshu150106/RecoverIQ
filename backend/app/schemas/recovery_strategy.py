from typing import Literal
from pydantic import BaseModel, Field

StrategyType = Literal[
    "SEND_SMART_RETRY_LINK",
    "SEND_PAYMENT_LINK",
    "SEND_REMINDER",
    "NO_ACTION",
    "HUMAN_REVIEW",
]


class RecoveryStrategyResponse(BaseModel):
    recovery_case_id: int = Field(..., description="Target RecoveryCase ID")
    strategy: StrategyType = Field(..., description="Deterministic recommended recovery strategy")
    reason: str = Field(..., description="Clear operational rationale for the recommended strategy")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Evaluated risk score (0-100)")
    recovery_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated recovery probability (0.0-1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in strategy evaluation (0.0-1.0)")
    requires_human_approval: bool = Field(..., description="Whether manual merchant operator sign-off is required before execution")
    allowed_to_execute: bool = Field(..., description="Whether this action is cleared by deterministic policy rules to run automatically")

    class Config:
        from_attributes = True
