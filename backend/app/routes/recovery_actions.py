from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.schemas.recovery_action import ExecuteLinkRequest, ExecuteLinkResponse
from app.policies.link_policy import link_safety_policy
from app.services.razorpay_client import razorpay_client, RazorpayClientError
from app.services.recovery_outcome import recovery_outcome_service

router = APIRouter(prefix="/api/recovery-cases", tags=["Recovery Actions"])


@router.post(
    "/{case_id}/execute-link",
    response_model=ExecuteLinkResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Razorpay Test Payment Link",
    description="Validates safety policies and generates a live Razorpay Test Mode Payment Link for an at-risk case."
)
def execute_payment_link(
    case_id: int,
    request: Optional[ExecuteLinkRequest] = None,
    db: Session = Depends(get_db)
) -> ExecuteLinkResponse:
    # 1. Fetch Case
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case with ID {case_id} not found."
        )

    # 2. Deterministic Safety Policy Gate
    allowed, policy_violation = link_safety_policy.validate(
        case=case,
        key_id=settings.RAZORPAY_KEY_ID,
        db=db
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=policy_violation
        )

    # 3. Calculate optional expiration timestamp (e.g. 24h)
    expire_hours = request.expire_hours if request else 24
    expire_timestamp = int((datetime.utcnow() + timedelta(hours=expire_hours)).timestamp())
    custom_desc = request.description if request else None

    # 4. Dispatch Razorpay Test API Call
    try:
        link_data = razorpay_client.create_payment_link(
            case=case,
            description=custom_desc,
            expire_by_timestamp=expire_timestamp
        )
    except RazorpayClientError as err:
        # Record failed action audit entry without modifying case status
        failed_action = RecoveryAction(
            recovery_case_id=case.id,
            action_type="CREATE_PAYMENT_LINK",
            status="FAILED",
            error_message=str(err),
            created_at=datetime.utcnow()
        )
        db.add(failed_action)
        recovery_outcome_service.create_pending_outcome(db, case.id, None, "SEND_PAYMENT_LINK")
        recovery_outcome_service.mark_failed(db, case.id, str(err))
        db.commit()

        raise HTTPException(
            status_code=err.status_code,
            detail=str(err)
        )
    except Exception as exc:
        failed_action = RecoveryAction(
            recovery_case_id=case.id,
            action_type="CREATE_PAYMENT_LINK",
            status="FAILED",
            error_message=f"Unexpected error: {str(exc)}",
            created_at=datetime.utcnow()
        )
        db.add(failed_action)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error creating payment link: {str(exc)}"
        )

    # 5. Success: Persist Action and Update Case Status to IN_PROGRESS
    action = RecoveryAction(
        recovery_case_id=case.id,
        action_type="CREATE_PAYMENT_LINK",
        status="EXECUTED",
        external_reference=link_data["id"],
        payment_link_id=link_data["id"],
        payment_link_url=link_data["short_url"],
        created_at=datetime.utcnow()
    )
    db.add(action)

    # Update case lifecycle status and record outcome tracking
    case.status = "IN_PROGRESS"
    db.commit()
    db.refresh(action)

    # Create pending outcome for analytics
    recovery_outcome_service.create_pending_outcome(
        db=db,
        case_id=case.id,
        action_id=action.id,
        strategy_type="SEND_PAYMENT_LINK"
    )

    return ExecuteLinkResponse(
        status="success",
        message=f"Razorpay Test Payment Link created successfully for Case #{case.id}.",
        recovery_case_id=case.id,
        action_id=action.id,
        payment_link_id=link_data["id"],
        payment_link_url=link_data["short_url"],
        amount=link_data["amount"],
        currency=link_data["currency"]
    )
