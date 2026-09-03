"""Deterministic Recovery Strategy Engine.

Given a RecoveryCase and its diagnostic signals, deterministically selects the
optimal recovery strategy strictly without calling external APIs or executing financial actions.
"""
from app.models.recovery_case import RecoveryCase
from app.schemas.recovery_strategy import RecoveryStrategyResponse, StrategyType


class RecoveryStrategyEngine:
    """Evaluates case heuristics against deterministic recovery policy rules."""

    TEMPORARY_FAILURE_KEYWORDS = [
        "timeout",
        "bank_timeout",
        "bank_authorization_timeout",
        "network",
        "network_error",
        "temporary",
        "temporary_failure",
        "bank_downtime",
        "issuer",
        "issuer_down",
        "system_error",
    ]

    @classmethod
    def evaluate(cls, case: RecoveryCase) -> RecoveryStrategyResponse:
        """Determines the appropriate recovery strategy deterministically."""
        
        status = (case.status or "").upper()
        risk = round(case.risk_score, 1)
        prob = round(case.recovery_probability, 2)
        confidence = round(case.confidence, 2)
        
        payment_event = case.payment_event
        amount = payment_event.amount if payment_event else 0
        failure_reason = (payment_event.failure_reason or "").lower() if payment_event else ""
        event_type = (payment_event.event_type or "").lower() if payment_event else ""

        # RULE B: NO_ACTION for resolved or terminal cases
        if status in ("RECOVERED", "CANCELLED", "EXPIRED"):
            return RecoveryStrategyResponse(
                recovery_case_id=case.id,
                strategy="NO_ACTION",
                reason=f"Case #{case.id} is already in terminal/resolved status '{status}'. No recovery outreach required.",
                risk_score=risk,
                recovery_probability=prob,
                confidence=confidence,
                requires_human_approval=False,
                allowed_to_execute=False,
            )

        # RULE A: HUMAN_REVIEW for high risk, very low recovery probability, or non-active status
        if risk >= 80.0 or prob < 0.30 or status not in ("DETECTED", "IN_PROGRESS") or amount > 5000000:
            reasons = []
            if risk >= 80.0:
                reasons.append(f"High risk score ({risk}/100)")
            if prob < 0.30:
                reasons.append(f"Low recovery probability ({int(prob*100)}%)")
            if amount > 5000000:
                reasons.append(f"Amount (Rs {amount/100:,.0f}) exceeds ₹50,000 policy safety cap")
            if status not in ("DETECTED", "IN_PROGRESS"):
                reasons.append(f"Unexpected status '{status}'")

            return RecoveryStrategyResponse(
                recovery_case_id=case.id,
                strategy="HUMAN_REVIEW",
                reason=f"Manual operator authorization required: {'; '.join(reasons)}.",
                risk_score=risk,
                recovery_probability=prob,
                confidence=confidence,
                requires_human_approval=True,
                allowed_to_execute=False,
            )

        # Check if failure appears clearly temporary / transient
        is_temporary = any(keyword in failure_reason for keyword in cls.TEMPORARY_FAILURE_KEYWORDS)

        # Check if previously dispatched link or expired/abandoned
        has_previous_actions = bool(case.recovery_actions and len(case.recovery_actions) > 0)
        is_expired_or_partial = event_type in ("payment_link.expired", "payment_link.partially_paid") or "expired" in failure_reason or "abandoned" in failure_reason

        # RULE C: SEND_SMART_RETRY_LINK for low risk + high probability + temporary failure
        if risk < 40.0 and prob >= 0.70 and is_temporary:
            return RecoveryStrategyResponse(
                recovery_case_id=case.id,
                strategy="SEND_SMART_RETRY_LINK",
                reason=f"Transient technical failure ({payment_event.failure_reason or 'temporary glitch'}) detected with low risk ({risk}/100) and strong recovery probability ({int(prob*100)}%). Instant automated retry link recommended.",
                risk_score=risk,
                recovery_probability=prob,
                confidence=confidence,
                requires_human_approval=False,
                allowed_to_execute=True,
            )

        # RULE E: SEND_REMINDER for expired/abandoned or previously engaged links
        if prob >= 0.40 and (is_expired_or_partial or has_previous_actions):
            return RecoveryStrategyResponse(
                recovery_case_id=case.id,
                strategy="SEND_REMINDER",
                reason=f"Payment link was previously created or expired/partially paid. Customer intent exists; automated gentle reminder notification recommended.",
                risk_score=risk,
                recovery_probability=prob,
                confidence=confidence,
                requires_human_approval=False,
                allowed_to_execute=True,
            )

        # RULE D: SEND_PAYMENT_LINK for standard moderate risk / standard recoverable failure
        if 40.0 <= risk <= 79.0 and prob >= 0.50 and amount <= 5000000:
            return RecoveryStrategyResponse(
                recovery_case_id=case.id,
                strategy="SEND_PAYMENT_LINK",
                reason=f"Standard recoverable failure within ₹50,000 policy limits (Risk: {risk}/100, Prob: {int(prob*100)}%). Generating new Razorpay Test Payment Link recommended.",
                risk_score=risk,
                recovery_probability=prob,
                confidence=confidence,
                requires_human_approval=False,
                allowed_to_execute=True,
            )

        # Default: Fallback to HUMAN_REVIEW if no specific automated pattern matched cleanly
        return RecoveryStrategyResponse(
            recovery_case_id=case.id,
            strategy="HUMAN_REVIEW",
            reason=f"Ambiguous or border risk profile (Risk: {risk}/100, Prob: {int(prob*100)}%). Operator review recommended before outreach.",
            risk_score=risk,
            recovery_probability=prob,
            confidence=confidence,
            requires_human_approval=True,
            allowed_to_execute=False,
        )


recovery_strategy_engine = RecoveryStrategyEngine()
