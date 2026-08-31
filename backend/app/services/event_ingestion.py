"""Event Ingestion Service.

Orchestrates event normalization, customer resolution, deduplication,
payment event logging, and automatic RecoveryCase generation for revenue-at-risk.
"""
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.payment_event import PaymentEvent
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.services.event_normalizer import event_normalizer
from app.services.recovery_scoring import recovery_scorer
from app.schemas.event import NormalizedEvent, EventIngestionResponse, PaymentEventResponse


class EventIngestionService:
    """Manages transactional event ingestion into RecoverIQ."""

    AT_RISK_EVENT_TYPES = {
        "payment.failed",
        "payment_link.expired",
        "payment_link.partially_paid",
    }

    SUCCESS_EVENT_TYPES = {
        "payment_link.paid",
        "payment.captured",
        "payment.authorized",
    }

    @classmethod
    def ingest_raw_event(
        cls,
        db: Session,
        raw_payload: Dict[str, Any]
    ) -> EventIngestionResponse:
        """Normalizes and ingests a raw event into the database."""
        
        # 1. Normalize
        normalized: NormalizedEvent = event_normalizer.normalize(raw_payload)

        # 2. Deduplication check on external_event_id
        if normalized.external_event_id:
            existing_event = db.query(PaymentEvent).filter(
                PaymentEvent.external_event_id == normalized.external_event_id
            ).first()
            if existing_event:
                existing_case = db.query(RecoveryCase).filter(
                    RecoveryCase.payment_event_id == existing_event.id
                ).first()
                return EventIngestionResponse(
                    status="success",
                    message="Duplicate event ignored (already recorded).",
                    is_duplicate=True,
                    payment_event=PaymentEventResponse.from_orm(existing_event),
                    recovery_case_id=existing_case.id if existing_case else None
                )

        # 3. Find or create Customer
        customer = db.query(Customer).filter(
            Customer.email == normalized.customer.email
        ).first()

        if not customer:
            customer = Customer(
                name=normalized.customer.name,
                email=normalized.customer.email,
                phone=normalized.customer.phone,
                total_transactions=0,
                successful_transactions=0,
                failed_transactions=0,
                total_paid=0,
                created_at=normalized.created_at
            )
            db.add(customer)
            db.flush()  # assign customer.id
        else:
            # Update phone if newly provided
            if normalized.customer.phone and not customer.phone:
                customer.phone = normalized.customer.phone

        # 4. Create PaymentEvent
        payment_event = PaymentEvent(
            customer_id=customer.id,
            event_type=normalized.event_type,
            amount=normalized.amount,
            currency=normalized.currency,
            status=normalized.status,
            failure_reason=normalized.failure_reason,
            external_event_id=normalized.external_event_id,
            created_at=normalized.created_at
        )
        db.add(payment_event)
        db.flush()  # assign payment_event.id

        # 5. Update Customer stats
        customer.total_transactions += 1

        is_at_risk = normalized.event_type in cls.AT_RISK_EVENT_TYPES
        is_success = normalized.event_type in cls.SUCCESS_EVENT_TYPES or normalized.status == "paid"

        if is_at_risk:
            customer.failed_transactions += 1
        elif is_success:
            customer.successful_transactions += 1
            customer.total_paid += normalized.amount

        # 6. For revenue-at-risk events, compute score and create RecoveryCase
        recovery_case_id = None
        if is_at_risk:
            scoring = recovery_scorer.evaluate(normalized, customer)

            recovery_case = RecoveryCase(
                customer_id=customer.id,
                payment_event_id=payment_event.id,
                risk_score=scoring["risk_score"],
                recovery_probability=scoring["recovery_probability"],
                recommended_action=scoring["recommended_action"],
                confidence=scoring["confidence"],
                status="DETECTED",
                created_at=normalized.created_at
            )
            db.add(recovery_case)
            db.flush()
            recovery_case_id = recovery_case.id

            # Create initial pending recovery action
            action = RecoveryAction(
                recovery_case_id=recovery_case.id,
                action_type=scoring["recommended_action"],
                status="PENDING",
                external_reference=None,
                created_at=normalized.created_at
            )
            db.add(action)

        db.commit()
        db.refresh(payment_event)

        return EventIngestionResponse(
            status="success",
            message="Event ingested successfully.",
            is_duplicate=False,
            payment_event=PaymentEventResponse.from_orm(payment_event),
            recovery_case_id=recovery_case_id
        )


event_ingestion_service = EventIngestionService()
