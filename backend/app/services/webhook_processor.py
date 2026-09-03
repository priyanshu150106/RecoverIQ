"""Razorpay Payment Link Webhook Processor Service.

Handles cryptographic signature verification, idempotency checking via x-razorpay-event-id,
transactional database updates with rollback safety, and outcome tracking.
"""
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.customer import Customer
from app.models.payment_event import PaymentEvent
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.services.recovery_outcome import recovery_outcome_service
from app.services.logging_service import structured_logger


class WebhookProcessingError(Exception):
    """Exception raised during webhook payload parsing or processing."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class WebhookProcessor:
    """Processes incoming Razorpay webhooks securely, transactionally, and idempotently."""

    SUPPORTED_EVENTS = {
        "payment_link.paid",
        "payment_link.partially_paid",
        "payment_link.cancelled",
        "payment_link.expired",
    }

    @classmethod
    def verify_signature(
        cls,
        raw_body: bytes,
        signature: Optional[str],
        secret: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """Cryptographically verifies HMAC-SHA256 signature over the raw HTTP body."""
        if not secret or not secret.strip():
            return False, "Webhook secret is not configured on the server."

        if not signature or not signature.strip():
            return False, "Missing X-Razorpay-Signature header."

        try:
            expected_signature = hmac.new(
                secret.strip().encode("utf-8"),
                raw_body,
                hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(expected_signature, signature.strip()):
                return True, None
            else:
                return False, "Invalid webhook signature."
        except Exception as exc:
            return False, f"Signature calculation failed: {str(exc)}"

    @classmethod
    def process_webhook(
        cls,
        db: Session,
        raw_body: bytes,
        signature: Optional[str],
        event_id: Optional[str]
    ) -> Dict[str, Any]:
        """Validates signature, checks idempotency via event_id, and processes lifecycle updates."""
        
        # 1. Signature Verification BEFORE JSON parsing
        is_valid, sig_error = cls.verify_signature(
            raw_body=raw_body,
            signature=signature,
            secret=settings.RECOVERIQ_WEBHOOK_SECRET
        )
        if not is_valid:
            structured_logger.warning(
                component="webhook_processor",
                operation="VERIFY_SIGNATURE",
                message=sig_error or "Signature verification failed",
                details={"event_id": event_id}
            )
            raise WebhookProcessingError(sig_error or "Signature verification failed.", status_code=400)

        # 2. Idempotency Header Check
        if not event_id or not event_id.strip():
            structured_logger.warning(
                component="webhook_processor",
                operation="CHECK_HEADER",
                message="Missing required header: X-Razorpay-Event-Id"
            )
            raise WebhookProcessingError(
                "Missing required header: X-Razorpay-Event-Id. Webhooks without event IDs are rejected.",
                status_code=400
            )

        clean_event_id = event_id.strip()

        # 3. Idempotency Deduplication Check
        existing_event = db.query(PaymentEvent).filter(
            PaymentEvent.external_event_id == clean_event_id
        ).first()

        if existing_event:
            structured_logger.info(
                component="webhook_processor",
                operation="CHECK_IDEMPOTENCY",
                message="Duplicate webhook event delivery ignored safely",
                event_id=clean_event_id
            )
            return {
                "status": "ignored",
                "message": "Duplicate event ignored (already processed).",
                "event_id": clean_event_id,
                "is_duplicate": True
            }

        # 4. JSON Payload Deserialization
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except Exception as exc:
            structured_logger.warning(
                component="webhook_processor",
                operation="PARSE_JSON",
                message=f"Malformed JSON payload: {str(exc)}"
            )
            raise WebhookProcessingError(f"Malformed JSON payload: {str(exc)}", status_code=400)

        event_name = payload.get("event")
        if not event_name:
            raise WebhookProcessingError("Missing 'event' field in webhook payload.", status_code=400)

        if event_name not in cls.SUPPORTED_EVENTS:
            structured_logger.info(
                component="webhook_processor",
                operation="FILTER_EVENT",
                message=f"Unsupported event '{event_name}' ignored",
                event_id=clean_event_id
            )
            return {
                "status": "ignored",
                "message": f"Unsupported event '{event_name}'.",
                "event": event_name,
                "event_id": clean_event_id
            }

        # 5. Extract Payment Link Entity
        plink_entity = (
            payload.get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
        )

        plink_id = plink_entity.get("id")
        if not plink_id:
            raise WebhookProcessingError(
                "Missing payment_link entity ID in webhook payload.",
                status_code=400
            )

        amount = plink_entity.get("amount", 0)
        amount_paid = plink_entity.get("amount_paid", amount)
        notes = plink_entity.get("notes", {}) or {}
        case_id_from_notes = notes.get("recoveriq_case_id")

        # 6. Locate RecoveryAction & Associated RecoveryCase
        action = (
            db.query(RecoveryAction)
            .filter(
                (RecoveryAction.payment_link_id == plink_id) |
                (RecoveryAction.external_reference == plink_id)
            )
            .first()
        )

        case = None
        if action:
            case = db.query(RecoveryCase).filter(RecoveryCase.id == action.recovery_case_id).first()

        # Fallback to notes if action match not found
        if not case and case_id_from_notes:
            try:
                cid = int(case_id_from_notes)
                case = db.query(RecoveryCase).filter(RecoveryCase.id == cid).first()
            except (ValueError, TypeError):
                pass

        if not case:
            # Record standalone event without failing webhook delivery
            dummy_customer = db.query(Customer).first()
            cust_id = dummy_customer.id if dummy_customer else 1
            orphan_event = PaymentEvent(
                customer_id=cust_id,
                event_type=event_name,
                amount=amount_paid or amount,
                currency="INR",
                status="unmatched",
                failure_reason=f"Webhook received for unknown payment link {plink_id}",
                external_event_id=clean_event_id,
                created_at=datetime.utcnow()
            )
            db.add(orphan_event)
            db.commit()

            structured_logger.info(
                component="webhook_processor",
                operation="MATCH_CASE",
                message=f"Payment link {plink_id} not associated with any active case",
                event_id=clean_event_id
            )

            return {
                "status": "unmatched",
                "message": f"Payment link {plink_id} not associated with any active RecoveryCase.",
                "event": event_name,
                "event_id": clean_event_id,
                "payment_link_id": plink_id
            }

        # 7. Apply Event-Specific Lifecycle Updates (with Transaction Rollback Safety)
        try:
            customer = case.customer

            if event_name == "payment_link.paid":
                # Fully recovered
                case.status = "RECOVERED"
                if customer:
                    customer.total_paid += amount_paid
                    customer.successful_transactions += 1

                new_event = PaymentEvent(
                    customer_id=case.customer_id,
                    event_type="payment_link.paid",
                    amount=amount_paid,
                    currency=case.payment_event.currency or "INR",
                    status="paid",
                    failure_reason=None,
                    external_event_id=clean_event_id,
                    created_at=datetime.utcnow()
                )
                db.add(new_event)
                recovery_outcome_service.mark_recovered(db, case.id, amount_paid)

            elif event_name == "payment_link.partially_paid":
                # Partial payment received - keep active in IN_PROGRESS
                case.status = "IN_PROGRESS"
                if customer:
                    customer.total_paid += amount_paid

                new_event = PaymentEvent(
                    customer_id=case.customer_id,
                    event_type="payment_link.partially_paid",
                    amount=amount_paid,
                    currency=case.payment_event.currency or "INR",
                    status="partially_paid",
                    failure_reason="partial_payment_received",
                    external_event_id=clean_event_id,
                    created_at=datetime.utcnow()
                )
                db.add(new_event)
                recovery_outcome_service.mark_partially_recovered(db, case.id, amount_paid)

            elif event_name == "payment_link.cancelled":
                # Cancelled - do not mark as recovered
                case.status = "CANCELLED"

                new_event = PaymentEvent(
                    customer_id=case.customer_id,
                    event_type="payment_link.cancelled",
                    amount=amount,
                    currency=case.payment_event.currency or "INR",
                    status="cancelled",
                    failure_reason="payment_link_cancelled_by_merchant",
                    external_event_id=clean_event_id,
                    created_at=datetime.utcnow()
                )
                db.add(new_event)
                recovery_outcome_service.mark_cancelled(db, case.id)

            elif event_name == "payment_link.expired":
                # Expired - do not mark as recovered
                new_event = PaymentEvent(
                    customer_id=case.customer_id,
                    event_type="payment_link.expired",
                    amount=amount,
                    currency=case.payment_event.currency or "INR",
                    status="expired",
                    failure_reason="payment_link_ttl_expired",
                    external_event_id=clean_event_id,
                    created_at=datetime.utcnow()
                )
                db.add(new_event)
                recovery_outcome_service.mark_expired(db, case.id)

            db.commit()
            db.refresh(case)

            structured_logger.info(
                component="webhook_processor",
                operation="UPDATE_CASE",
                message=f"Webhook processed successfully for Case #{case.id}",
                case_id=case.id,
                event_id=clean_event_id,
                details={"event": event_name, "case_status": case.status}
            )

        except Exception as err:
            db.rollback()
            structured_logger.error(
                component="webhook_processor",
                operation="TRANSACTION_ROLLBACK",
                message="Error during webhook database update, transaction rolled back safely",
                case_id=case.id if case else None,
                event_id=clean_event_id,
                details={"error": str(err)}
            )
            raise WebhookProcessingError(f"Database error during webhook processing: {str(err)}", status_code=500)

        return {
            "status": "success",
            "message": f"Webhook processed successfully for Case #{case.id}.",
            "event": event_name,
            "event_id": clean_event_id,
            "payment_link_id": plink_id,
            "recovery_case_id": case.id,
            "case_status": case.status
        }


webhook_processor = WebhookProcessor()
