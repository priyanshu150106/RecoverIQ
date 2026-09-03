"""Hackathon Demo Mode Simulation Routes.

Allows judges and operators to simulate payment link completions and end-to-end
recovery lifecycle state transitions without moving real funds or calling Razorpay Live mode.
"""
import time
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.recovery_case import RecoveryCase
from app.models.payment_event import PaymentEvent
from app.models.recovery_action import RecoveryAction

router = APIRouter(prefix="/api/demo", tags=["Demo & Simulation"])


@router.post(
    "/recovery/{case_id}/simulate-payment",
    status_code=status.HTTP_200_OK,
    summary="Simulate Successful Demo Payment",
    description="Simulates a verified payment completion for a case with an active payment link in Demo Mode."
)
def simulate_demo_payment(
    case_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # 1. Verify case exists
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case with ID {case_id} not found."
        )

    # 2. Verify case has an active payment link action
    active_action = (
        db.query(RecoveryAction)
        .filter(
            RecoveryAction.recovery_case_id == case.id,
            RecoveryAction.status == "EXECUTED",
            (RecoveryAction.payment_link_id.isnot(None) | RecoveryAction.payment_link_url.isnot(None))
        )
        .first()
    )

    if not active_action:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot simulate payment: Case #{case.id} does not have an active payment link. Please generate a Razorpay link first."
        )

    # 3. Idempotency Check: if already RECOVERED, return success without double-crediting
    if case.status == "RECOVERED":
        return {
            "status": "success",
            "demo": True,
            "is_duplicate": True,
            "message": f"Case #{case.id} is already recovered (idempotent demo execution).",
            "recovery_case_id": case.id,
            "amount_recovered": case.payment_event.amount,
            "currency": case.payment_event.currency or "INR",
            "case_status": "RECOVERED"
        }

    # 4. Verify case state is eligible
    if case.status not in ("DETECTED", "IN_PROGRESS"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot simulate payment for case in status '{case.status}'."
        )

    # 5. Process Demo Lifecycle Updates (mirroring webhook resolution)
    amount = case.payment_event.amount
    customer = case.customer

    case.status = "RECOVERED"
    if customer:
        customer.total_paid += amount
        customer.successful_transactions += 1

    sim_event_id = f"demo_sim_pay_{case.id}_{int(time.time() * 1000)}"
    new_event = PaymentEvent(
        customer_id=case.customer_id,
        event_type="payment_link.paid",
        amount=amount,
        currency=case.payment_event.currency or "INR",
        status="paid",
        failure_reason=None,
        external_event_id=sim_event_id,
        created_at=datetime.utcnow()
    )
    db.add(new_event)
    db.commit()
    db.refresh(case)

    return {
        "status": "success",
        "demo": True,
        "is_duplicate": False,
        "message": f"Demo payment simulated successfully for Case #{case.id}. Revenue marked as recovered.",
        "recovery_case_id": case.id,
        "payment_event_id": new_event.id,
        "amount_recovered": amount,
        "currency": case.payment_event.currency or "INR",
        "case_status": case.status
    }
