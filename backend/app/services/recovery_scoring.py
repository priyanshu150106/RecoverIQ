"""Deterministic Baseline Recovery Scoring Service.

Provides transparent, rule-based scoring of revenue risk and recovery probability
based on customer history, failure reasons, transaction size, and event type.
This deterministic service will serve as the baseline comparator for Stage 4 AI reasoning.
"""
from typing import Dict, Any, Tuple
from app.models.customer import Customer
from app.schemas.event import NormalizedEvent


class RecoveryScorer:
    """Calculates baseline risk scores and recommended recovery actions deterministically."""

    @classmethod
    def evaluate(
        cls,
        event: NormalizedEvent,
        customer: Customer = None
    ) -> Dict[str, Any]:
        """Calculates risk_score (0-100), recovery_probability (0-1), action, and confidence."""
        
        reason = (event.failure_reason or "").lower()
        event_type = event.event_type.lower()
        amount_inr = event.amount / 100.0  # convert paise to INR for human thresholding

        # 1. Base scores from failure reason and event type
        if "timeout" in reason or "network" in reason or "issuer" in reason or "bank_downtime" in reason:
            base_risk = 28.0
            base_prob = 0.88
            action = "SEND_SMART_RETRY_LINK"
            confidence = 0.92
            reason_category = "Temporary Bank / Network Glitch"

        elif event_type == "payment_link.partially_paid":
            base_risk = 20.0
            base_prob = 0.92
            action = "SCHEDULE_WHATSAPP_REMINDER"
            confidence = 0.95
            reason_category = "Partial Payment (Committed Buyer)"

        elif event_type == "payment_link.expired" or "expired" in reason:
            base_risk = 42.0
            base_prob = 0.72
            action = "EXTEND_PAYMENT_LINK_24H"
            confidence = 0.88
            reason_category = "Payment Link Expiry"

        elif "insufficient" in reason or "balance" in reason:
            base_risk = 58.0
            base_prob = 0.58
            action = "FALLBACK_UPI_INTENT"
            confidence = 0.82
            reason_category = "Insufficient Balance (Alternative Method Needed)"

        elif "expired_card" in reason or "card_declined" in reason or "do_not_honor" in reason:
            base_risk = 68.0
            base_prob = 0.45
            action = "SEND_UPDATE_PAYMENT_METHOD_LINK"
            confidence = 0.85
            reason_category = "Card Auth Rejection"

        elif "fraud" in reason or "blocked" in reason or "stolen" in reason:
            base_risk = 92.0
            base_prob = 0.10
            action = "FLAG_MANUAL_REVIEW"
            confidence = 0.96
            reason_category = "High Risk / Security Flag"

        else:
            base_risk = 50.0
            base_prob = 0.60
            action = "SEND_RETRY_LINK"
            confidence = 0.75
            reason_category = "Generic Failure"

        # 2. Customer Historical Profile Adjustments
        history_delta_risk = 0.0
        history_delta_prob = 0.0
        history_note = "New customer (no historical baseline)"

        if customer and customer.total_transactions > 0:
            success_rate = customer.successful_transactions / customer.total_transactions
            if customer.successful_transactions >= 2 and success_rate >= 0.75:
                # Loyal returning customer with strong history
                history_delta_risk -= 12.0
                history_delta_prob += 0.12
                history_note = f"Loyal customer ({customer.successful_transactions} past successes, {int(success_rate*100)}% rate)"
            elif customer.failed_transactions >= 2 and success_rate < 0.40:
                # Customer with repeated payment difficulties
                history_delta_risk += 16.0
                history_delta_prob -= 0.15
                history_note = f"Repeat failure history ({customer.failed_transactions} failures)"
                if base_prob < 0.4:
                    action = "FLAG_MANUAL_REVIEW"
            else:
                history_note = f"Moderate customer history ({customer.total_transactions} transactions)"

        # 3. Transaction Amount Bracket Adjustments
        amount_note = "Standard ticket size"
        if amount_inr < 1500:
            # Low friction recovery
            history_delta_prob += 0.05
            amount_note = "Low-ticket transaction (low buyer friction)"
        elif amount_inr > 20000:
            # High value at risk - requires extra care
            history_delta_risk += 8.0
            amount_note = "High-value transaction (>Rs 20,000)"
            if action != "FLAG_MANUAL_REVIEW" and base_prob < 0.65:
                action = "OFFER_FLEXIBLE_PAYMENT_OPTION"

        # 4. Final clamp calculations
        final_risk = max(5.0, min(95.0, round(base_risk + history_delta_risk, 1)))
        final_prob = max(0.05, min(0.98, round(base_prob + history_delta_prob, 2)))
        final_confidence = round(confidence, 2)

        return {
            "risk_score": final_risk,
            "recovery_probability": final_prob,
            "recommended_action": action,
            "confidence": final_confidence,
            "scoring_breakdown": {
                "category": reason_category,
                "customer_history": history_note,
                "amount_context": amount_note,
                "model": "deterministic_baseline_v1"
            }
        }


recovery_scorer = RecoveryScorer()
