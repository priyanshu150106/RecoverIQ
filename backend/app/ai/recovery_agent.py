"""AI Recovery Agent Service.

Leverages OpenAI models (e.g. gpt-4o-mini) to reason on payment failure signals,
customer transaction history, and behavioral risk to produce structured recovery recommendations.
Includes automatic fallback to deterministic scoring if OpenAI is offline, unconfigured, or returns invalid data.
"""
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.config import settings
from app.models.recovery_case import RecoveryCase
from app.schemas.ai_recommendation import (
    AIRecoveryRecommendation,
    AIRecoveryRecommendationResponse,
)
from app.services.recovery_scoring import recovery_scorer
from app.schemas.event import NormalizedEvent, NormalizedCustomerInfo


class AIRecoveryAgent:
    """Autonomous AI Agent for Razorpay Revenue Recovery Recommendations."""

    SYSTEM_PROMPT = """You are RecoverIQ AI, an elite revenue recovery intelligence agent for Razorpay merchants.
Your role is to analyze payment failure events, customer transaction profiles, and risk heuristics to recommend the optimal, safest revenue recovery strategy.

You MUST respond with a single valid JSON object strictly matching this schema:
{
  "recovery_probability": float (between 0.0 and 1.0, probability that revenue can be recovered),
  "recommended_action": string (one of: "SEND_SMART_RETRY_LINK", "FALLBACK_UPI_INTENT", "EXTEND_PAYMENT_LINK_24H", "SCHEDULE_WHATSAPP_REMINDER", "SEND_UPDATE_PAYMENT_METHOD_LINK", "FLAG_MANUAL_REVIEW", "OFFER_FLEXIBLE_PAYMENT_OPTION"),
  "urgency": string (strictly one of: "LOW", "MEDIUM", "HIGH"),
  "confidence": float (between 0.0 and 1.0, agent confidence in this diagnosis),
  "reasoning": string (concise 2-3 sentence explanation detailing why this action fits the customer and failure context),
  "signals": list of strings (3-5 key diagnostic bullet points extracted from customer history and failure code),
  "policy_recommendation": string (strictly one of: "ALLOW", "BLOCK", "REVIEW")
}

Guidelines:
- If failure is a bank timeout or network glitch and customer is loyal, recommend high probability, high urgency retry link ("ALLOW").
- If failure is an expired payment link, recommend extending payment link by 24h.
- If failure is insufficient funds, recommend UPI fallback with medium urgency.
- If transaction amount is very high (>Rs 50,000) or repeat fraud patterns exist, recommend "REVIEW" or "BLOCK".
- Be professional, precise, and operations-focused."""

    @classmethod
    def build_sanitized_context(cls, case: RecoveryCase) -> Dict[str, Any]:
        """Extracts strictly anonymized business and risk signals (no PII, no secrets)."""
        customer = case.customer
        payment_event = case.payment_event

        amount_inr = round(payment_event.amount / 100, 2)
        total_tx = customer.total_transactions if customer else 0
        success_tx = customer.successful_transactions if customer else 0
        failed_tx = customer.failed_transactions if customer else 0
        total_paid_inr = round(customer.total_paid / 100, 2) if customer else 0.0
        success_rate = round((success_tx / total_tx) * 100, 1) if total_tx > 0 else 0.0

        previous_actions = [a.action_type for a in case.recovery_actions] if case.recovery_actions else []

        return {
            "case_id": case.id,
            "transaction_amount_inr": amount_inr,
            "currency": payment_event.currency or "INR",
            "event_type": payment_event.event_type,
            "failure_reason": payment_event.failure_reason or "unspecified",
            "customer_history": {
                "total_transactions": total_tx,
                "successful_transactions": success_tx,
                "failed_transactions": failed_tx,
                "success_rate_percentage": success_rate,
                "total_lifetime_spent_inr": total_paid_inr
            },
            "baseline_heuristics": {
                "risk_score_0_to_100": case.risk_score,
                "baseline_recovery_probability": case.recovery_probability,
                "baseline_recommended_action": case.recommended_action
            },
            "previous_recovery_actions_attempted": previous_actions
        }

    @classmethod
    def generate_fallback(cls, case: RecoveryCase) -> AIRecoveryRecommendationResponse:
        """Constructs a validated deterministic recommendation when AI is unavailable."""
        customer = case.customer
        payment_event = case.payment_event
        reason = (payment_event.failure_reason or "").lower()
        amount_inr = payment_event.amount / 100.0

        # Calculate rule-based urgency
        if "timeout" in reason or "network" in reason or payment_event.event_type == "payment_link.expired":
            urgency = "HIGH"
        elif "insufficient" in reason or case.risk_score > 60:
            urgency = "MEDIUM"
        else:
            urgency = "LOW"

        # Calculate advisory policy suggestion
        if payment_event.amount > 5000000:  # > Rs 50,000
            policy_rec = "BLOCK"
        elif case.risk_score > 75:
            policy_rec = "REVIEW"
        else:
            policy_rec = "ALLOW"

        # Extract deterministic signals
        signals = [
            f"{customer.successful_transactions} past successful transactions ({int((customer.successful_transactions / customer.total_transactions * 100) if customer.total_transactions > 0 else 0)}% success rate)",
            f"Lifetime captured revenue of Rs {customer.total_paid / 100:,.0f}",
            f"Failure root cause identified as: {payment_event.failure_reason or 'unspecified'}",
            f"Baseline risk magnitude evaluated at {case.risk_score}/100"
        ]

        if payment_event.amount > 2000000:
            signals.append("High-ticket transaction requiring monitored outreach")
        elif payment_event.amount < 150000:
            signals.append("Low friction impulsive recovery threshold (<Rs 1,500)")

        reasoning = (
            f"Deterministic Baseline Analysis: Recovery strategy formulated based on customer transaction profile "
            f"({customer.successful_transactions} past successes), failure reason '{payment_event.failure_reason or 'general'}', "
            f"and transaction size Rs {amount_inr:,.0f}."
        )

        rec = AIRecoveryRecommendation(
            recovery_probability=case.recovery_probability,
            recommended_action=case.recommended_action,
            urgency=urgency,
            confidence=case.confidence,
            reasoning=reasoning,
            signals=signals,
            policy_recommendation=policy_rec
        )

        return AIRecoveryRecommendationResponse(
            status="success",
            recovery_case_id=case.id,
            source="fallback",
            model_used=None,
            recommendation=rec
        )

    @classmethod
    def generate_recommendation(
        cls,
        case: RecoveryCase,
        client: Optional[OpenAI] = None
    ) -> AIRecoveryRecommendationResponse:
        """Generates structured AI recommendation via OpenAI with automatic deterministic fallback."""
        
        api_key = (settings.OPENAI_API_KEY or "").strip()

        # If no client passed and no API key configured, use deterministic fallback
        if not client and not api_key:
            return cls.generate_fallback(case)

        # Build sanitized contextual prompt
        sanitized_context = cls.build_sanitized_context(case)

        try:
            openai_client = client or OpenAI(api_key=api_key)
            model_name = settings.OPENAI_MODEL or "gpt-4o-mini"

            response = openai_client.chat.completions.create(
                model=model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": cls.SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Analyze this payment failure and recommend optimal recovery strategy:\n{json.dumps(sanitized_context, indent=2)}"
                    }
                ],
                temperature=0.2,
                timeout=15.0
            )

            raw_content = response.choices[0].message.content
            parsed_json = json.loads(raw_content)

            # Validate structured fields using Pydantic
            validated_rec = AIRecoveryRecommendation.model_validate(parsed_json)

            return AIRecoveryRecommendationResponse(
                status="success",
                recovery_case_id=case.id,
                source="ai",
                model_used=model_name,
                recommendation=validated_rec
            )

        except Exception as exc:
            # On any failure (API error, timeout, malformed output, validation error), fall back safely
            fallback_response = cls.generate_fallback(case)
            return fallback_response


ai_recovery_agent = AIRecoveryAgent()
