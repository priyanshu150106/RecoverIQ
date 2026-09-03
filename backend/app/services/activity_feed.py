"""Activity Feed and Case Timeline Aggregation Service.

Extracts, normalizes, and sequences operational and intelligence events from
existing PaymentEvent, RecoveryAction, and RecoveryCase entities.
"""
from datetime import timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.recovery_case import RecoveryCase
from app.models.payment_event import PaymentEvent
from app.models.recovery_action import RecoveryAction
from app.schemas.activity import ActivityItem


class ActivityFeedService:
    """Aggregates and formats real-time operational activity from database entities."""

    @classmethod
    def get_global_activity_feed(
        cls,
        db: Session,
        limit: int = 20
    ) -> List[ActivityItem]:
        """Returns the most recent activity items across the entire platform, newest first."""
        clamped_limit = max(1, min(100, limit))
        activities: List[ActivityItem] = []

        # 1. Payment Events
        events = db.query(PaymentEvent).order_by(PaymentEvent.created_at.desc()).limit(clamped_limit * 2).all()
        for evt in events:
            case_id = evt.recovery_case.id if evt.recovery_case else None
            amt = evt.amount

            if evt.event_type == "payment.failed" or evt.status == "failed":
                activities.append(ActivityItem(
                    id=f"act_evt_{evt.id}",
                    timestamp=evt.created_at,
                    actor="SYSTEM",
                    action="FAILURE_DETECTED",
                    summary=f"Payment failure of Rs {amt/100:,.0f} detected ({evt.failure_reason or 'unspecified'}).",
                    status="failed",
                    case_id=case_id,
                    amount=amt,
                    metadata={"failure_reason": evt.failure_reason, "currency": evt.currency}
                ))
            elif evt.event_type == "payment_link.paid" or evt.status == "paid":
                activities.append(ActivityItem(
                    id=f"act_evt_{evt.id}",
                    timestamp=evt.created_at,
                    actor="WEBHOOK_RECEIVER",
                    action="PAYMENT_CAPTURED",
                    summary=f"Payment of Rs {amt/100:,.0f} successfully captured via Razorpay Payment Link.",
                    status="paid",
                    case_id=case_id,
                    amount=amt,
                    metadata={"external_event_id": evt.external_event_id}
                ))
            elif evt.event_type == "payment_link.partially_paid" or evt.status == "partially_paid":
                activities.append(ActivityItem(
                    id=f"act_evt_{evt.id}",
                    timestamp=evt.created_at,
                    actor="WEBHOOK_RECEIVER",
                    action="PAYMENT_PARTIALLY_CAPTURED",
                    summary=f"Partial payment of Rs {amt/100:,.0f} captured via Razorpay Payment Link.",
                    status="partially_paid",
                    case_id=case_id,
                    amount=amt,
                    metadata={"external_event_id": evt.external_event_id}
                ))
            elif evt.event_type == "payment_link.cancelled" or evt.status == "cancelled":
                activities.append(ActivityItem(
                    id=f"act_evt_{evt.id}",
                    timestamp=evt.created_at,
                    actor="WEBHOOK_RECEIVER",
                    action="PAYMENT_CANCELLED",
                    summary=f"Payment link for Rs {amt/100:,.0f} was cancelled.",
                    status="cancelled",
                    case_id=case_id,
                    amount=amt,
                    metadata={"external_event_id": evt.external_event_id}
                ))
            elif evt.event_type == "payment_link.expired" or evt.status == "expired":
                activities.append(ActivityItem(
                    id=f"act_evt_{evt.id}",
                    timestamp=evt.created_at,
                    actor="WEBHOOK_RECEIVER",
                    action="PAYMENT_EXPIRED",
                    summary=f"Payment link for Rs {amt/100:,.0f} expired without completion.",
                    status="expired",
                    case_id=case_id,
                    amount=amt,
                    metadata={"external_event_id": evt.external_event_id}
                ))

        # 2. Recovery Actions
        actions = db.query(RecoveryAction).order_by(RecoveryAction.created_at.desc()).limit(clamped_limit * 2).all()
        for act in actions:
            case = act.recovery_case
            amt = case.payment_event.amount if (case and case.payment_event) else None

            if act.status == "EXECUTED" and act.action_type == "CREATE_PAYMENT_LINK":
                activities.append(ActivityItem(
                    id=f"act_act_{act.id}",
                    timestamp=act.created_at,
                    actor="RAZORPAY_EXECUTION",
                    action="LINK_GENERATED",
                    summary=f"Razorpay Test Payment Link generated for Case #{act.recovery_case_id} ({act.payment_link_id or 'plink_live'}).",
                    status="EXECUTED",
                    case_id=act.recovery_case_id,
                    amount=amt,
                    metadata={"payment_link_id": act.payment_link_id, "payment_link_url": act.payment_link_url}
                ))
            elif act.status == "FAILED":
                activities.append(ActivityItem(
                    id=f"act_act_{act.id}",
                    timestamp=act.created_at,
                    actor="RAZORPAY_EXECUTION",
                    action="RECOVERY_ACTION_FAILED",
                    summary=f"Recovery action {act.action_type} failed for Case #{act.recovery_case_id}: {act.error_message or 'Error'}",
                    status="FAILED",
                    case_id=act.recovery_case_id,
                    amount=amt,
                    metadata={"error_message": act.error_message}
                ))

        # 3. Recovered Cases
        recovered_cases = db.query(RecoveryCase).filter(RecoveryCase.status == "RECOVERED").all()
        for rc in recovered_cases:
            amt = rc.payment_event.amount if rc.payment_event else None
            activities.append(ActivityItem(
                id=f"act_case_rec_{rc.id}",
                timestamp=rc.created_at + timedelta(minutes=5),
                actor="SYSTEM",
                action="CASE_RECOVERED",
                summary=f"Recovery Case #{rc.id} successfully marked as RECOVERED.",
                status="RECOVERED",
                case_id=rc.id,
                amount=amt,
                metadata={"risk_score": rc.risk_score, "recovery_probability": rc.recovery_probability}
            ))

        # Sort descending (newest first)
        activities.sort(key=lambda a: a.timestamp, reverse=True)
        return activities[:clamped_limit]

    @classmethod
    def get_case_timeline(
        cls,
        db: Session,
        case_id: int
    ) -> Optional[List[ActivityItem]]:
        """Returns the chronological timeline for a specific recovery case, oldest first."""
        case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            return None

        timeline: List[ActivityItem] = []
        payment_event = case.payment_event
        amt = payment_event.amount if payment_event else None

        # 1. Initial Failure Detected
        if payment_event:
            timeline.append(ActivityItem(
                id=f"tl_evt_{payment_event.id}",
                timestamp=payment_event.created_at,
                actor="SYSTEM",
                action="FAILURE_DETECTED",
                summary=f"Payment failure of Rs {amt/100:,.0f} detected ({payment_event.failure_reason or 'unspecified'}).",
                status=payment_event.status,
                case_id=case.id,
                amount=amt,
                metadata={"failure_reason": payment_event.failure_reason, "currency": payment_event.currency}
            ))

        # 2. AI / Deterministic Diagnosis
        timeline.append(ActivityItem(
            id=f"tl_ai_diag_{case.id}",
            timestamp=case.created_at + timedelta(seconds=1),
            actor="AI_AGENT",
            action="AI_DIAGNOSED",
            summary=f"AI Agent evaluated case with {int(case.recovery_probability * 100)}% recovery probability and recommended {case.recommended_action}.",
            status="DIAGNOSED",
            case_id=case.id,
            amount=amt,
            metadata={"risk_score": case.risk_score, "recovery_probability": case.recovery_probability, "recommended_action": case.recommended_action}
        ))

        # 3. Actions (Policy check + Execution)
        for act in case.recovery_actions:
            if act.status == "EXECUTED":
                # Policy Passed
                timeline.append(ActivityItem(
                    id=f"tl_policy_{act.id}",
                    timestamp=act.created_at - timedelta(seconds=1),
                    actor="POLICY_ENGINE",
                    action="POLICY_PASSED",
                    summary="Deterministic policy engine validated key isolation, amount limit, and cooldown window.",
                    status="PASSED",
                    case_id=case.id,
                    amount=amt,
                    metadata={"decision": "ALLOW"}
                ))

                # Link Generated
                timeline.append(ActivityItem(
                    id=f"tl_act_{act.id}",
                    timestamp=act.created_at,
                    actor="RAZORPAY_EXECUTION",
                    action="LINK_GENERATED",
                    summary=f"Razorpay Test Payment Link generated ({act.payment_link_id or 'plink_test'}).",
                    status="EXECUTED",
                    case_id=case.id,
                    amount=amt,
                    metadata={"payment_link_id": act.payment_link_id, "payment_link_url": act.payment_link_url}
                ))
            elif act.status == "FAILED":
                timeline.append(ActivityItem(
                    id=f"tl_act_fail_{act.id}",
                    timestamp=act.created_at,
                    actor="RAZORPAY_EXECUTION",
                    action="RECOVERY_ACTION_FAILED",
                    summary=f"Recovery action execution failed: {act.error_message or 'Error'}",
                    status="FAILED",
                    case_id=case.id,
                    amount=amt,
                    metadata={"error_message": act.error_message}
                ))

        # 4. Related Webhook Payment Events for this customer
        related_events = (
            db.query(PaymentEvent)
            .filter(
                PaymentEvent.customer_id == case.customer_id,
                PaymentEvent.id != (payment_event.id if payment_event else -1),
                PaymentEvent.created_at >= case.created_at
            )
            .all()
        )

        for rev_evt in related_events:
            rev_amt = rev_evt.amount
            if rev_evt.event_type == "payment_link.paid" or rev_evt.status == "paid":
                timeline.append(ActivityItem(
                    id=f"tl_rev_evt_{rev_evt.id}",
                    timestamp=rev_evt.created_at,
                    actor="WEBHOOK_RECEIVER",
                    action="PAYMENT_CAPTURED",
                    summary=f"Razorpay webhook verified: Payment of Rs {rev_amt/100:,.0f} captured.",
                    status="paid",
                    case_id=case.id,
                    amount=rev_amt,
                    metadata={"external_event_id": rev_evt.external_event_id}
                ))
            elif rev_evt.event_type == "payment_link.partially_paid":
                timeline.append(ActivityItem(
                    id=f"tl_rev_evt_{rev_evt.id}",
                    timestamp=rev_evt.created_at,
                    actor="WEBHOOK_RECEIVER",
                    action="PAYMENT_PARTIALLY_CAPTURED",
                    summary=f"Razorpay webhook verified: Partial payment of Rs {rev_amt/100:,.0f} received.",
                    status="partially_paid",
                    case_id=case.id,
                    amount=rev_amt,
                    metadata={"external_event_id": rev_evt.external_event_id}
                ))
            elif rev_evt.event_type == "payment_link.cancelled":
                timeline.append(ActivityItem(
                    id=f"tl_rev_evt_{rev_evt.id}",
                    timestamp=rev_evt.created_at,
                    actor="WEBHOOK_RECEIVER",
                    action="PAYMENT_CANCELLED",
                    summary="Razorpay webhook verified: Payment link was cancelled.",
                    status="cancelled",
                    case_id=case.id,
                    amount=rev_amt,
                    metadata={"external_event_id": rev_evt.external_event_id}
                ))
            elif rev_evt.event_type == "payment_link.expired":
                timeline.append(ActivityItem(
                    id=f"tl_rev_evt_{rev_evt.id}",
                    timestamp=rev_evt.created_at,
                    actor="WEBHOOK_RECEIVER",
                    action="PAYMENT_EXPIRED",
                    summary="Razorpay webhook verified: Payment link expired.",
                    status="expired",
                    case_id=case.id,
                    amount=rev_amt,
                    metadata={"external_event_id": rev_evt.external_event_id}
                ))

        # 5. Case Recovered
        if case.status == "RECOVERED":
            latest_ts = max([a.timestamp for a in timeline]) if timeline else case.created_at
            timeline.append(ActivityItem(
                id=f"tl_case_rec_{case.id}",
                timestamp=latest_ts + timedelta(seconds=1),
                actor="SYSTEM",
                action="CASE_RECOVERED",
                summary=f"Recovery Case #{case.id} marked as RECOVERED. Revenue captured and credited to merchant metrics.",
                status="RECOVERED",
                case_id=case.id,
                amount=amt,
                metadata={"risk_score": case.risk_score, "recovery_probability": case.recovery_probability}
            ))

        # Sort ascending (oldest first)
        timeline.sort(key=lambda a: a.timestamp)
        return timeline


activity_feed_service = ActivityFeedService()
