from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.models.recovery_case import RecoveryCase
from app.models.payment_event import PaymentEvent
from app.models.recovery_action import RecoveryAction
from app.models.recovery_approval import RecoveryApproval

router = APIRouter(prefix="/api/system", tags=["System Observability & Health"])


@router.get(
    "/readiness",
    status_code=status.HTTP_200_OK,
    summary="System Readiness Check",
    description="Verifies database connectivity and subsystems configuration states without exposing secrets."
)
def get_system_readiness(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # 1. Database connectivity
    db_healthy = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False

    # 2. Razorpay configuration
    razorpay_configured = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_ID.startswith("rzp_test_"))
    razorpay_mode = "test_mode" if razorpay_configured else "unconfigured"

    # 3. OpenAI configuration state (without key exposure)
    openai_configured = "configured" if bool(settings.OPENAI_API_KEY) else "unconfigured"

    # 4. Webhook secret state (without secret exposure)
    webhook_configured = "configured" if bool(settings.RECOVERIQ_WEBHOOK_SECRET) else "unconfigured"

    overall_status = "ready" if (db_healthy and razorpay_configured) else "degraded"

    return {
        "status": overall_status,
        "database": "healthy" if db_healthy else "unavailable",
        "razorpay": razorpay_mode,
        "openai": openai_configured,
        "webhook": webhook_configured,
        "environment": settings.ENVIRONMENT,
    }


@router.get(
    "/metrics",
    status_code=status.HTTP_200_OK,
    summary="System Operational Metrics",
    description="Returns aggregate operational telemetry across cases, webhooks, approvals, and actions."
)
def get_system_operational_metrics(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    total_cases = db.query(RecoveryCase).count()
    detected_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "DETECTED").count()
    in_progress_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "IN_PROGRESS").count()
    recovered_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "RECOVERED").count()
    cancelled_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "CANCELLED").count()
    expired_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "EXPIRED").count()

    total_events = db.query(PaymentEvent).count()
    total_actions = db.query(RecoveryAction).count()
    successful_links = db.query(RecoveryAction).filter(RecoveryAction.status == "EXECUTED").count()
    failed_links = db.query(RecoveryAction).filter(RecoveryAction.status == "FAILED").count()

    pending_approvals = db.query(RecoveryApproval).filter(RecoveryApproval.status == "PENDING").count()
    approved_approvals = db.query(RecoveryApproval).filter(RecoveryApproval.status == "APPROVED").count()
    rejected_approvals = db.query(RecoveryApproval).filter(RecoveryApproval.status == "REJECTED").count()
    executed_approvals = db.query(RecoveryApproval).filter(RecoveryApproval.status == "EXECUTED").count()

    return {
        "total_recovery_cases": total_cases,
        "detected_cases": detected_cases,
        "in_progress_cases": in_progress_cases,
        "recovered_cases": recovered_cases,
        "cancelled_cases": cancelled_cases,
        "expired_cases": expired_cases,
        "total_payment_events": total_events,
        "total_recovery_actions": total_actions,
        "successful_payment_links": successful_links,
        "failed_payment_links": failed_links,
        "pending_approvals": pending_approvals,
        "approved_approvals": approved_approvals,
        "rejected_approvals": rejected_approvals,
        "executed_approvals": executed_approvals,
    }
