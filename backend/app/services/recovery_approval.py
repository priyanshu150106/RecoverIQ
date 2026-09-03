"""Human-in-the-Loop Recovery Approval & Execution Service.

Provides a secure workflow where operator approval is explicitly requested, granted,
or rejected, followed by deterministic policy re-verification prior to invoking
existing Razorpay Test Mode execution infrastructure.
"""
from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.recovery_case import RecoveryCase
from app.models.recovery_approval import RecoveryApproval
from app.models.recovery_action import RecoveryAction
from app.schemas.recovery_approval import ApprovalExecutionResponse
from app.services.razorpay_client import razorpay_client, RazorpayClientError
from app.services.recovery_strategy import recovery_strategy_engine
from app.policies.link_policy import link_safety_policy
from app.services.recovery_outcome import recovery_outcome_service
from app.services.logging_service import structured_logger


class RecoveryApprovalService:
    """Manages operator approvals and safe execution of recovery actions."""

    @classmethod
    def request_approval(
        cls,
        db: Session,
        case_id: int,
        strategy: str,
        requested_by: str = "merchant_operator"
    ) -> RecoveryApproval:
        """Creates a PENDING approval request for a recovery case."""
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recovery case with ID {case_id} not found."
            )

        if case.status in ("RECOVERED", "CANCELLED", "EXPIRED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot request approval for case in terminal status '{case.status}'."
            )

        # Prevent duplicate pending approvals for the same case
        existing_pending = (
            db.query(RecoveryApproval)
            .filter(
                RecoveryApproval.recovery_case_id == case.id,
                RecoveryApproval.status == "PENDING"
            )
            .first()
        )
        if existing_pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A pending approval request (ID #{existing_pending.id}) already exists for Case #{case.id}."
            )

        approval = RecoveryApproval(
            recovery_case_id=case.id,
            strategy_type=strategy,
            requested_by=requested_by,
            status="PENDING",
            reason=f"Operator approval requested for {strategy}."
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)

        structured_logger.info(
            component="approval_service",
            operation="REQUEST_APPROVAL",
            message=f"Approval requested for Case #{case.id} strategy {strategy}",
            case_id=case.id,
            approval_id=approval.id,
            details={"strategy": strategy, "requested_by": requested_by}
        )

        return approval

    @classmethod
    def approve_approval(
        cls,
        db: Session,
        approval_id: int,
        approved_by: str = "merchant_operator",
        reason: Optional[str] = None
    ) -> RecoveryApproval:
        """Transitions approval from PENDING to APPROVED."""
        approval = db.query(RecoveryApproval).filter(RecoveryApproval.id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request with ID {approval_id} not found."
            )

        if approval.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve: Approval #{approval_id} is in status '{approval.status}' (must be PENDING)."
            )

        approval.status = "APPROVED"
        approval.approved_by = approved_by
        approval.approved_at = datetime.utcnow()
        if reason:
            approval.reason = reason

        db.commit()
        db.refresh(approval)

        structured_logger.info(
            component="approval_service",
            operation="APPROVE_APPROVAL",
            message=f"Approval #{approval.id} APPROVED by {approved_by}",
            case_id=approval.recovery_case_id,
            approval_id=approval.id,
            details={"approved_by": approved_by}
        )

        return approval

    @classmethod
    def reject_approval(
        cls,
        db: Session,
        approval_id: int,
        rejected_by: str = "merchant_operator",
        reason: Optional[str] = None
    ) -> RecoveryApproval:
        """Transitions approval from PENDING to REJECTED."""
        approval = db.query(RecoveryApproval).filter(RecoveryApproval.id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request with ID {approval_id} not found."
            )

        if approval.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject: Approval #{approval_id} is in status '{approval.status}' (must be PENDING)."
            )

        approval.status = "REJECTED"
        approval.approved_by = rejected_by
        approval.rejected_at = datetime.utcnow()
        approval.reason = reason or "Rejected by merchant operator"

        db.commit()
        db.refresh(approval)

        structured_logger.info(
            component="approval_service",
            operation="REJECT_APPROVAL",
            message=f"Approval #{approval.id} REJECTED by {rejected_by}",
            case_id=approval.recovery_case_id,
            approval_id=approval.id,
            details={"rejected_by": rejected_by, "reason": approval.reason}
        )

        return approval

    @classmethod
    def execute_approved_action(
        cls,
        db: Session,
        approval_id: int,
        expire_hours: int = 24
    ) -> ApprovalExecutionResponse:
        """Executes an approved strategy after full deterministic safety re-verification."""
        approval = db.query(RecoveryApproval).filter(RecoveryApproval.id == approval_id).first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request with ID {approval_id} not found."
            )

        if approval.status != "APPROVED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot execute: Approval #{approval_id} is in status '{approval.status}' (must be APPROVED)."
            )

        case = approval.recovery_case
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated RecoveryCase #{approval.recovery_case_id} not found."
            )

        # 1. Re-run Deterministic Link Safety Policy
        is_valid, violation_msg = link_safety_policy.validate(case=case, db=db)
        if not is_valid:
            structured_logger.warning(
                component="approval_service",
                operation="POLICY_GATE_RECHECK",
                message=f"Policy gate rejection during approved execution: {violation_msg}",
                case_id=case.id,
                approval_id=approval.id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Policy Gate Violation: {violation_msg}"
            )

        # 2. Re-run Strategy Engine Verification
        strat_eval = recovery_strategy_engine.evaluate(case=case)
        if strat_eval.strategy == "NO_ACTION" or case.status in ("RECOVERED", "CANCELLED", "EXPIRED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Case status is no longer eligible for recovery execution ({case.status})."
            )

        customer = case.customer
        payment_event = case.payment_event

        # 3. Execute approved action
        if approval.strategy_type in ("SEND_PAYMENT_LINK", "SEND_SMART_RETRY_LINK"):
            try:
                link_result = razorpay_client.create_payment_link(
                    amount=payment_event.amount,
                    customer_name=customer.name,
                    customer_email=customer.email,
                    customer_phone=customer.phone,
                    description=f"RecoverIQ Payment Link - Case #{case.id}",
                    expire_hours=expire_hours,
                    notes={
                        "recoveriq_case_id": case.id,
                        "customer_id": case.customer_id,
                        "strategy": approval.strategy_type,
                        "approval_id": approval.id,
                    }
                )
            except RazorpayClientError as e:
                # Record failed action
                failed_act = RecoveryAction(
                    recovery_case_id=case.id,
                    action_type=approval.strategy_type,
                    status="FAILED",
                    error_message=str(e),
                )
                db.add(failed_act)
                recovery_outcome_service.create_pending_outcome(db, case.id, None, approval.strategy_type)
                recovery_outcome_service.mark_failed(db, case.id, str(e))
                db.commit()

                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Razorpay link creation failed: {str(e)}"
                )

            # Persist successful action and update status
            action = RecoveryAction(
                recovery_case_id=case.id,
                action_type=approval.strategy_type,
                status="EXECUTED",
                external_reference=link_result["payment_link_id"],
                payment_link_id=link_result["payment_link_id"],
                payment_link_url=link_result["payment_link_url"],
            )
            case.status = "IN_PROGRESS"
            approval.status = "EXECUTED"
            approval.executed_at = datetime.utcnow()

            db.add(action)
            db.commit()
            db.refresh(action)

            # Record outcome tracking
            recovery_outcome_service.create_pending_outcome(
                db=db,
                case_id=case.id,
                action_id=action.id,
                strategy_type=approval.strategy_type
            )

            structured_logger.info(
                component="approval_service",
                operation="EXECUTE_APPROVED",
                message=f"Approved strategy {approval.strategy_type} EXECUTED successfully for Case #{case.id}",
                case_id=case.id,
                approval_id=approval.id,
                recovery_action_id=action.id
            )

            return ApprovalExecutionResponse(
                approval_id=approval.id,
                recovery_case_id=case.id,
                strategy_type=approval.strategy_type,
                status="EXECUTED",
                action_id=action.id,
                payment_link_id=link_result["payment_link_id"],
                payment_link_url=link_result["payment_link_url"],
                message="Approved strategy executed: Razorpay Test Payment Link generated successfully."
            )

        elif approval.strategy_type == "SEND_REMINDER":
            action = RecoveryAction(
                recovery_case_id=case.id,
                action_type="SEND_REMINDER",
                status="EXECUTED",
                error_message=None,
            )
            case.status = "IN_PROGRESS"
            approval.status = "EXECUTED"
            approval.executed_at = datetime.utcnow()

            db.add(action)
            db.commit()
            db.refresh(action)

            recovery_outcome_service.create_pending_outcome(
                db=db,
                case_id=case.id,
                action_id=action.id,
                strategy_type=approval.strategy_type
            )

            structured_logger.info(
                component="approval_service",
                operation="EXECUTE_APPROVED",
                message=f"Approved reminder outreach logged for Case #{case.id}",
                case_id=case.id,
                approval_id=approval.id,
                recovery_action_id=action.id
            )

            return ApprovalExecutionResponse(
                approval_id=approval.id,
                recovery_case_id=case.id,
                strategy_type=approval.strategy_type,
                status="EXECUTED",
                action_id=action.id,
                payment_link_id=None,
                payment_link_url=None,
                message="Approved reminder strategy logged and marked as executed."
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Strategy '{approval.strategy_type}' is consultative and cannot be executed automatically."
            )


recovery_approval_service = RecoveryApprovalService()
