from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.recovery_case import RecoveryCase
from app.models.payment_event import PaymentEvent
from app.models.customer import Customer
from app.schemas.recovery_case import (
    RecoveryCaseListItem,
    RecoveryCaseDetailResponse,
    RecoveryActionResponse
)
from app.schemas.customer import CustomerResponse
from app.schemas.event import PaymentEventResponse
from app.services.recovery_scoring import recovery_scorer
from app.schemas.event import NormalizedEvent, NormalizedCustomerInfo

router = APIRouter(prefix="/api/recovery-cases", tags=["Recovery Cases"])


@router.get(
    "",
    response_model=List[RecoveryCaseListItem],
    summary="List Recovery Cases",
    description="Returns all revenue recovery cases with optional status filtering."
)
def list_recovery_cases(
    status: Optional[str] = Query(None, description="Filter by case status (e.g. DETECTED, IN_PROGRESS, RECOVERED)"),
    db: Session = Depends(get_db)
) -> List[RecoveryCaseListItem]:
    query = db.query(RecoveryCase).join(Customer).join(PaymentEvent).order_by(RecoveryCase.created_at.desc())

    if status:
        query = query.filter(RecoveryCase.status == status.upper())

    cases = query.all()
    results = []

    for c in cases:
        results.append(RecoveryCaseListItem(
            id=c.id,
            customer_id=c.customer_id,
            customer_name=c.customer.name,
            customer_email=c.customer.email,
            customer_phone=c.customer.phone,
            amount=c.payment_event.amount,
            currency=c.payment_event.currency,
            event_type=c.payment_event.event_type,
            failure_reason=c.payment_event.failure_reason,
            risk_score=c.risk_score,
            recovery_probability=c.recovery_probability,
            recommended_action=c.recommended_action,
            confidence=c.confidence,
            status=c.status,
            created_at=c.created_at
        ))

    return results


@router.get(
    "/{case_id}",
    response_model=RecoveryCaseDetailResponse,
    summary="Get Recovery Case Detail",
    description="Returns detailed case diagnostic information, customer profile, scoring reasoning, and recovery actions."
)
def get_recovery_case(
    case_id: int,
    db: Session = Depends(get_db)
) -> RecoveryCaseDetailResponse:
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case with ID {case_id} not found."
        )

    # Reconstruct scoring breakdown context
    normalized = NormalizedEvent(
        event_type=case.payment_event.event_type,
        customer=NormalizedCustomerInfo(
            name=case.customer.name,
            email=case.customer.email,
            phone=case.customer.phone
        ),
        amount=case.payment_event.amount,
        currency=case.payment_event.currency,
        status=case.payment_event.status,
        failure_reason=case.payment_event.failure_reason,
        created_at=case.payment_event.created_at
    )
    scoring_eval = recovery_scorer.evaluate(normalized, case.customer)

    return RecoveryCaseDetailResponse(
        id=case.id,
        customer_id=case.customer_id,
        payment_event_id=case.payment_event_id,
        risk_score=case.risk_score,
        recovery_probability=case.recovery_probability,
        recommended_action=case.recommended_action,
        confidence=case.confidence,
        status=case.status,
        created_at=case.created_at,
        customer=CustomerResponse.from_orm(case.customer),
        payment_event=PaymentEventResponse.from_orm(case.payment_event),
        recovery_actions=[RecoveryActionResponse.from_orm(a) for a in case.recovery_actions],
        scoring_breakdown=scoring_eval.get("scoring_breakdown")
    )
