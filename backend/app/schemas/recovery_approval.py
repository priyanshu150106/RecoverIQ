from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

ApprovalStatus = Literal["PENDING", "APPROVED", "REJECTED", "EXECUTED", "EXPIRED"]


class CreateApprovalRequest(BaseModel):
    strategy: str = Field(..., description="Recovery strategy code for which approval is requested")
    requested_by: str = Field("merchant_operator", description="Operator or subsystem requesting approval")


class ApprovalDecisionRequest(BaseModel):
    decided_by: str = Field("merchant_operator", description="Merchant operator identity approving or rejecting")
    reason: Optional[str] = Field(None, description="Optional justification for the approval or rejection decision")


class RecoveryApprovalResponse(BaseModel):
    id: int = Field(..., description="Approval record ID")
    recovery_case_id: int = Field(..., description="Target RecoveryCase ID")
    strategy_type: str = Field(..., description="Strategy type under review")
    requested_by: str = Field(..., description="Entity that requested approval")
    approved_by: Optional[str] = Field(None, description="Operator that approved or rejected")
    status: ApprovalStatus = Field(..., description="Current lifecycle state of the approval request")
    reason: Optional[str] = Field(None, description="Decision explanation or note")
    created_at: datetime = Field(..., description="UTC creation timestamp")
    approved_at: Optional[datetime] = Field(None, description="UTC approval timestamp")
    rejected_at: Optional[datetime] = Field(None, description="UTC rejection timestamp")
    executed_at: Optional[datetime] = Field(None, description="UTC execution timestamp")

    class Config:
        from_attributes = True


class ApprovalExecutionResponse(BaseModel):
    approval_id: int = Field(..., description="Approval ID executed")
    recovery_case_id: int = Field(..., description="Target RecoveryCase ID")
    strategy_type: str = Field(..., description="Strategy executed")
    status: str = Field(..., description="Outcome status")
    action_id: Optional[int] = Field(None, description="Created RecoveryAction ID")
    payment_link_id: Optional[str] = Field(None, description="Razorpay Test Payment Link ID")
    payment_link_url: Optional[str] = Field(None, description="Razorpay Test Payment Link URL")
    message: str = Field(..., description="Operational result message")

    class Config:
        from_attributes = True
