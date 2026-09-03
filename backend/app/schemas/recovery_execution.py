from typing import Optional, Literal
from pydantic import BaseModel, Field
from app.schemas.recovery_strategy import StrategyType

ExecutionStatus = Literal["EXECUTED", "BLOCKED", "FAILED", "QUEUED"]


class ExecuteStrategyRequest(BaseModel):
    expire_hours: int = Field(24, ge=1, le=720, description="Expiry duration in hours for generated payment link")


class ExecuteStrategyResponse(BaseModel):
    case_id: int = Field(..., description="Target RecoveryCase ID")
    strategy: StrategyType = Field(..., description="Deterministic strategy evaluated")
    allowed: bool = Field(..., description="Whether execution was permitted by safety policy")
    requires_approval: bool = Field(..., description="Whether manual merchant approval is required")
    execution_status: ExecutionStatus = Field(..., description="Status result of the orchestration attempt")
    action_type: Optional[str] = Field(None, description="Recovery action type executed")
    action_id: Optional[int] = Field(None, description="ID of created RecoveryAction record")
    payment_link_id: Optional[str] = Field(None, description="Razorpay Test Payment Link ID if generated")
    payment_link_url: Optional[str] = Field(None, description="Razorpay Test Payment Link URL if generated")
    reason: str = Field(..., description="Safety gate rationale or execution summary")
    message: str = Field(..., description="Human-readable operational status message")

    class Config:
        from_attributes = True
