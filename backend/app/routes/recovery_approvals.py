from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.recovery_approval import RecoveryApproval
from app.schemas.recovery_approval import (
    CreateApprovalRequest,
    ApprovalDecisionRequest,
    RecoveryApprovalResponse,
    ApprovalExecutionResponse,
)
from app.services.recovery_approval import recovery_approval_service

router = APIRouter(tags=["Human-in-the-Loop Approvals"])


@router.post(
    "/api/recovery-cases/{case_id}/approval",
    response_model=RecoveryApprovalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request Operator Approval for Recovery Strategy",
    description="Submits a pending Human-in-the-Loop approval request for an evaluated recovery strategy on a case."
)
def request_case_approval(
    case_id: int,
    payload: CreateApprovalRequest,
    db: Session = Depends(get_db)
) -> RecoveryApprovalResponse:
    approval = recovery_approval_service.request_approval(
        db=db,
        case_id=case_id,
        strategy=payload.strategy,
        requested_by=payload.requested_by,
    )
    return approval


@router.get(
    "/api/recovery-cases/{case_id}/approvals",
    response_model=List[RecoveryApprovalResponse],
    status_code=status.HTTP_200_OK,
    summary="Get All Approval Records for a Case",
    description="Returns the history of approval requests, decisions, and execution records for a specific case."
)
def get_case_approvals(
    case_id: int,
    db: Session = Depends(get_db)
) -> List[RecoveryApprovalResponse]:
    approvals = (
        db.query(RecoveryApproval)
        .filter(RecoveryApproval.recovery_case_id == case_id)
        .order_by(RecoveryApproval.created_at.desc())
        .all()
    )
    return approvals


@router.get(
    "/api/approvals/pending",
    response_model=List[RecoveryApprovalResponse],
    status_code=status.HTTP_200_OK,
    summary="List All Pending Approval Requests",
    description="Returns all currently pending Human-in-the-Loop approval requests across the recovery pipeline."
)
def get_pending_approvals(
    db: Session = Depends(get_db)
) -> List[RecoveryApprovalResponse]:
    pending = (
        db.query(RecoveryApproval)
        .filter(RecoveryApproval.status == "PENDING")
        .order_by(RecoveryApproval.created_at.desc())
        .all()
    )
    return pending


@router.post(
    "/api/approvals/{approval_id}/approve",
    response_model=RecoveryApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve Recovery Strategy Request",
    description="Merchant operator approves a pending recovery strategy request."
)
def approve_recovery_approval(
    approval_id: int,
    payload: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    db: Session = Depends(get_db)
) -> RecoveryApprovalResponse:
    approval = recovery_approval_service.approve_approval(
        db=db,
        approval_id=approval_id,
        approved_by=payload.decided_by,
        reason=payload.reason,
    )
    return approval


@router.post(
    "/api/approvals/{approval_id}/reject",
    response_model=RecoveryApprovalResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject Recovery Strategy Request",
    description="Merchant operator rejects a pending recovery strategy request with an audit reason."
)
def reject_recovery_approval(
    approval_id: int,
    payload: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    db: Session = Depends(get_db)
) -> RecoveryApprovalResponse:
    approval = recovery_approval_service.reject_approval(
        db=db,
        approval_id=approval_id,
        rejected_by=payload.decided_by,
        reason=payload.reason,
    )
    return approval


@router.post(
    "/api/approvals/{approval_id}/execute",
    response_model=ApprovalExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Approved Recovery Action",
    description="Executes an approved strategy after re-running deterministic policy gates against Razorpay Test Mode."
)
def execute_approved_recovery_action(
    approval_id: int,
    db: Session = Depends(get_db)
) -> ApprovalExecutionResponse:
    result = recovery_approval_service.execute_approved_action(
        db=db,
        approval_id=approval_id,
    )
    return result
