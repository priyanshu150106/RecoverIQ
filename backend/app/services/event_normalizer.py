"""Event Normalization Service.

Converts heterogeneous or raw incoming event dictionaries into a standard
internal NormalizedEvent model. Independent of gateway-specific implementations.
"""
from datetime import datetime
from typing import Dict, Any
from app.schemas.event import NormalizedEvent, NormalizedCustomerInfo


class EventNormalizer:
    """Normalizes raw payment events into a consistent internal structure."""

    SUPPORTED_EVENT_TYPES = {
        "payment.failed",
        "payment_link.expired",
        "payment_link.partially_paid",
        "payment_link.paid",
        "payment.captured",
        "payment.authorized"
    }

    @classmethod
    def normalize(cls, raw: Dict[str, Any]) -> NormalizedEvent:
        """Accepts a raw event dict and returns a standardized NormalizedEvent."""
        event_type = raw.get("event_type", "unknown").lower().strip()
        
        # Normalize customer details
        raw_cust = raw.get("customer") or {}
        email = raw_cust.get("email") or raw.get("email") or raw.get("customer_email") or "customer@example.com"
        name = raw_cust.get("name") or raw.get("name") or raw.get("customer_name") or email.split("@")[0].title()
        phone = raw_cust.get("phone") or raw.get("phone") or raw.get("customer_phone") or None

        customer_info = NormalizedCustomerInfo(
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone.strip() if phone else None
        )

        # Normalize amount (ensure integer paise)
        raw_amount = raw.get("amount", 0)
        try:
            amount = int(raw_amount)
        except (ValueError, TypeError):
            amount = 0

        # Currency
        currency = raw.get("currency", "INR").upper()

        # Status mapping
        status = raw.get("status")
        if not status:
            if event_type == "payment.failed":
                status = "failed"
            elif event_type == "payment_link.expired":
                status = "expired"
            elif event_type == "payment_link.partially_paid":
                status = "partially_paid"
            elif event_type in ("payment_link.paid", "payment.captured", "payment.authorized"):
                status = "paid"
            else:
                status = "unknown"

        # Failure reason
        failure_reason = raw.get("failure_reason") or raw.get("error_description") or raw.get("reason")
        if not failure_reason and status == "failed":
            failure_reason = "general_payment_failure"
        elif not failure_reason and status == "expired":
            failure_reason = "payment_link_ttl_expired"

        # External Event ID
        external_event_id = raw.get("external_event_id") or raw.get("id") or raw.get("event_id")

        # Timestamp
        raw_time = raw.get("created_at")
        if isinstance(raw_time, datetime):
            created_at = raw_time
        elif isinstance(raw_time, str):
            try:
                created_at = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.utcnow()
        elif isinstance(raw_time, (int, float)):
            try:
                created_at = datetime.utcfromtimestamp(raw_time)
            except Exception:
                created_at = datetime.utcnow()
        else:
            created_at = datetime.utcnow()

        return NormalizedEvent(
            event_type=event_type,
            customer=customer_info,
            amount=amount,
            currency=currency,
            status=status,
            failure_reason=failure_reason,
            external_event_id=external_event_id,
            created_at=created_at
        )


event_normalizer = EventNormalizer()
