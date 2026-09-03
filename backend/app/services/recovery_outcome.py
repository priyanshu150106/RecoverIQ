"""Deterministic Recovery Outcome Tracking Service.

Records and updates measurable lifecycle outcomes for every recovery strategy execution.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.recovery_case import RecoveryCase
from app.models.recovery_outcome import RecoveryOutcome


class RecoveryOutcomeService:
    """Manages creation and outcome transitions of recovery strategy attempts."""

    @classmethod
    def calculate_recovery_percentage(cls, amount_at_risk: int, amount_recovered: int) -> float:
        """Calculates recovery percentage safely, handling zero-division."""
        if amount_at_risk <= 0:
            return 0.0
        pct = (amount_recovered / amount_at_risk) * 100.0
        return round(min(100.0, max(0.0, pct)), 2)

    @classmethod
    def calculate_time_to_recovery(cls, execution_timestamp: datetime, recovery_timestamp: datetime) -> float:
        """Calculates elapsed recovery seconds without fabricating timestamps."""
        if not execution_timestamp or not recovery_timestamp:
            return 0.0
        elapsed = (recovery_timestamp - execution_timestamp).total_seconds()
        return round(max(0.0, elapsed), 2)

    @classmethod
    def create_pending_outcome(
        cls,
        db: Session,
        case_id: int,
        action_id: Optional[int],
        strategy_type: str,
        execution_time: Optional[datetime] = None
    ) -> RecoveryOutcome:
        """Initializes a PENDING outcome record when an action is executed."""
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        amount_at_risk = case.payment_event.amount if (case and case.payment_event) else 0

        outcome = RecoveryOutcome(
            recovery_case_id=case_id,
            recovery_action_id=action_id,
            strategy_type=strategy_type,
            outcome_status="PENDING",
            amount_at_risk=amount_at_risk,
            amount_recovered=0,
            recovery_percentage=0.0,
            execution_timestamp=execution_time or datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(outcome)
        db.commit()
        db.refresh(outcome)
        return outcome

    @classmethod
    def mark_recovered(
        cls,
        db: Session,
        case_id: int,
        amount_recovered: int,
        recovery_time: Optional[datetime] = None
    ) -> Optional[RecoveryOutcome]:
        """Marks the outcome as RECOVERED upon full payment confirmation."""
        outcome = (
            db.query(RecoveryOutcome)
            .filter(RecoveryOutcome.recovery_case_id == case_id)
            .order_by(RecoveryOutcome.created_at.desc())
            .first()
        )
        rec_time = recovery_time or datetime.utcnow()

        if not outcome:
            # Fallback creation if not explicitly created prior
            case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
            amount_at_risk = case.payment_event.amount if (case and case.payment_event) else amount_recovered
            strat = case.recommended_action if case else "SEND_PAYMENT_LINK"
            outcome = RecoveryOutcome(
                recovery_case_id=case_id,
                strategy_type=strat,
                amount_at_risk=amount_at_risk,
                execution_timestamp=case.created_at if case else rec_time,
                created_at=datetime.utcnow()
            )
            db.add(outcome)

        outcome.outcome_status = "RECOVERED"
        outcome.amount_recovered = amount_recovered
        outcome.recovery_percentage = cls.calculate_recovery_percentage(outcome.amount_at_risk, amount_recovered)
        outcome.recovery_timestamp = rec_time
        outcome.time_to_recovery_seconds = cls.calculate_time_to_recovery(outcome.execution_timestamp, rec_time)

        db.commit()
        db.refresh(outcome)
        return outcome

    @classmethod
    def mark_partially_recovered(
        cls,
        db: Session,
        case_id: int,
        amount_recovered: int,
        recovery_time: Optional[datetime] = None
    ) -> Optional[RecoveryOutcome]:
        """Marks the outcome as PARTIALLY_RECOVERED upon partial payment."""
        outcome = (
            db.query(RecoveryOutcome)
            .filter(RecoveryOutcome.recovery_case_id == case_id)
            .order_by(RecoveryOutcome.created_at.desc())
            .first()
        )
        rec_time = recovery_time or datetime.utcnow()

        if not outcome:
            case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
            amount_at_risk = case.payment_event.amount if (case and case.payment_event) else amount_recovered
            strat = case.recommended_action if case else "SEND_PAYMENT_LINK"
            outcome = RecoveryOutcome(
                recovery_case_id=case_id,
                strategy_type=strat,
                amount_at_risk=amount_at_risk,
                execution_timestamp=case.created_at if case else rec_time,
                created_at=datetime.utcnow()
            )
            db.add(outcome)

        outcome.outcome_status = "PARTIALLY_RECOVERED"
        outcome.amount_recovered = amount_recovered
        outcome.recovery_percentage = cls.calculate_recovery_percentage(outcome.amount_at_risk, amount_recovered)
        outcome.recovery_timestamp = rec_time
        outcome.time_to_recovery_seconds = cls.calculate_time_to_recovery(outcome.execution_timestamp, rec_time)

        db.commit()
        db.refresh(outcome)
        return outcome

    @classmethod
    def mark_failed(
        cls,
        db: Session,
        case_id: int,
        reason: Optional[str] = None
    ) -> Optional[RecoveryOutcome]:
        """Marks the outcome as FAILED."""
        outcome = (
            db.query(RecoveryOutcome)
            .filter(RecoveryOutcome.recovery_case_id == case_id)
            .order_by(RecoveryOutcome.created_at.desc())
            .first()
        )
        if outcome:
            outcome.outcome_status = "FAILED"
            db.commit()
            db.refresh(outcome)
        return outcome

    @classmethod
    def mark_expired(
        cls,
        db: Session,
        case_id: int
    ) -> Optional[RecoveryOutcome]:
        """Marks the outcome as EXPIRED."""
        outcome = (
            db.query(RecoveryOutcome)
            .filter(RecoveryOutcome.recovery_case_id == case_id)
            .order_by(RecoveryOutcome.created_at.desc())
            .first()
        )
        if outcome:
            outcome.outcome_status = "EXPIRED"
            db.commit()
            db.refresh(outcome)
        return outcome

    @classmethod
    def mark_cancelled(
        cls,
        db: Session,
        case_id: int
    ) -> Optional[RecoveryOutcome]:
        """Marks the outcome as CANCELLED."""
        outcome = (
            db.query(RecoveryOutcome)
            .filter(RecoveryOutcome.recovery_case_id == case_id)
            .order_by(RecoveryOutcome.created_at.desc())
            .first()
        )
        if outcome:
            outcome.outcome_status = "CANCELLED"
            db.commit()
            db.refresh(outcome)
        return outcome


recovery_outcome_service = RecoveryOutcomeService()
