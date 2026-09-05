"""Deterministic Safety Policy for Payment Link Generation.

Enforces strict safety guardrails before executing any Razorpay Test API calls:
1. Test Mode Key Isolation (strictly starts with 'rzp_test_')
2. Valid Case Lifecycle State (DETECTED or IN_PROGRESS only)
3. Maximum Transaction Value Cap (<= Rs 50,000 / 5,000,000 paise)
4. Anti-Spam / Cooldown Window (No duplicate active link created within 30 minutes)
"""
from datetime import datetime, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction


class LinkSafetyPolicy:
    """Enforces deterministic safety rules on payment link creation."""

    MAX_AMOUNT_PAISE: int = 5000000  # Rs 50,000 in paise
    COOLDOWN_MINUTES: int = 30
    VALID_CASE_STATUSES = {"DETECTED", "IN_PROGRESS"}

    @classmethod
    def validate(
        cls,
        case: RecoveryCase,
        key_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validates all safety policies. Returns (allowed, error_reason)."""

        if key_id is None:
            from app.config import settings
            key_id = settings.RAZORPAY_KEY_ID

        # Policy 1: Test Mode Key Check
        if not key_id or not key_id.strip():
            return False, "Policy Gate Violation: Razorpay Key ID is not configured in environment."

        clean_key = key_id.strip()
        if not clean_key.startswith("rzp_test_"):
            return False, (
                "Policy Gate Violation: Only Razorpay Test Mode keys (starting with 'rzp_test_') are allowed. "
                "Live or invalid keys are blocked."
            )

        # Policy 2: Case Lifecycle State Check
        if not case.status or case.status.upper() not in cls.VALID_CASE_STATUSES:
            return False, (
                f"Policy Gate Violation: Case #{case.id} is in status '{case.status}'. "
                f"Payment links can only be generated for cases in DETECTED or IN_PROGRESS status."
            )

        # Policy 3: Transaction Amount Cap Check
        amount = case.payment_event.amount if case.payment_event else 0
        if amount > cls.MAX_AMOUNT_PAISE:
            amount_inr = amount / 100
            max_inr = cls.MAX_AMOUNT_PAISE / 100
            return False, (
                f"Policy Gate Violation: Case amount (Rs {amount_inr:,.0f}) exceeds the safety cap "
                f"of Rs {max_inr:,.0f}. Manual authorization is required for high-value recoveries."
            )

        # Policy 4: Cooldown Window Check (No active link created within 30 minutes)
        if db:
            cutoff_time = datetime.utcnow() - timedelta(minutes=cls.COOLDOWN_MINUTES)
            recent_action = (
                db.query(RecoveryAction)
                .filter(
                    RecoveryAction.recovery_case_id == case.id,
                    RecoveryAction.action_type.in_(["CREATE_PAYMENT_LINK", "SEND_PAYMENT_LINK", "SEND_SMART_RETRY_LINK"]),
                    RecoveryAction.status == "EXECUTED",
                    RecoveryAction.created_at >= cutoff_time
                )
                .first()
            )

            if recent_action:
                mins_ago = int((datetime.utcnow() - recent_action.created_at).total_seconds() / 60)
                return False, (
                    f"Policy Gate Violation: A payment link was already created {mins_ago} minutes ago. "
                    f"Cooldown period of {cls.COOLDOWN_MINUTES} minutes is in effect."
                )

        # All policies passed
        return True, None


link_safety_policy = LinkSafetyPolicy()
