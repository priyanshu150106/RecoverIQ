"""Razorpay Test Mode API Client.

Interfaces securely with the official Razorpay Payment Links API in Test Mode.
Credentials are read strictly from backend environment settings and never logged or exposed.
"""
from typing import Dict, Any, Optional
import httpx
from app.config import settings
from app.models.recovery_case import RecoveryCase


class RazorpayClientError(Exception):
    """Custom exception for Razorpay API integration failures."""
    def __init__(self, message: str, status_code: int = 502, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_details = error_details or {}


class RazorpayClient:
    """Handles communications with Razorpay Test Mode REST endpoints."""

    BASE_URL = "https://api.razorpay.com/v1"

    @classmethod
    def create_payment_link(
        cls,
        case: RecoveryCase,
        description: Optional[str] = None,
        expire_by_timestamp: Optional[int] = None
    ) -> Dict[str, Any]:
        """Creates a Razorpay Test Mode Payment Link for an at-risk recovery case."""
        
        key_id = (settings.RAZORPAY_KEY_ID or "").strip()
        key_secret = (settings.RAZORPAY_KEY_SECRET or "").strip()

        if not key_id or not key_secret:
            raise RazorpayClientError(
                "Razorpay API credentials are not configured on the server.",
                status_code=500
            )

        if not key_id.startswith("rzp_test_"):
            raise RazorpayClientError(
                "Safety Violation: Non-test key detected. Refusing to call financial API in Live Mode.",
                status_code=403
            )

        customer = case.customer
        payment_event = case.payment_event
        amount_paise = payment_event.amount
        
        # Prepare request payload
        link_description = description or f"RecoverIQ Payment Recovery for Case #{case.id}"
        
        payload: Dict[str, Any] = {
            "amount": amount_paise,
            "currency": payment_event.currency or "INR",
            "accept_partial": False,
            "description": link_description,
            "customer": {
                "name": customer.name,
                "email": customer.email,
            },
            "notify": {
                "sms": False,
                "email": False
            },
            "reminder_enable": False,
            "notes": {
                "recoveriq_case_id": str(case.id),
                "customer_id": str(customer.id),
                "event_type": payment_event.event_type,
                "source": "RecoverIQ Stage 3A Test Recovery"
            }
        }

        if customer.phone:
            payload["customer"]["contact"] = customer.phone

        if expire_by_timestamp:
            payload["expire_by"] = expire_by_timestamp

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{cls.BASE_URL}/payment_links",
                    json=payload,
                    auth=(key_id, key_secret),
                    headers={"Content-Type": "application/json"}
                )

            if response.status_code not in (200, 201):
                err_body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_body.get("error", {}).get("description") or f"HTTP {response.status_code}: {response.text}"
                raise RazorpayClientError(
                    f"Razorpay Payment Link API error: {err_msg}",
                    status_code=502,
                    error_details=err_body
                )

            data = response.json()
            return {
                "id": data.get("id"),
                "short_url": data.get("short_url"),
                "status": data.get("status"),
                "amount": data.get("amount"),
                "currency": data.get("currency", "INR"),
                "created_at": data.get("created_at")
            }

        except httpx.RequestError as exc:
            raise RazorpayClientError(
                f"Network communication failure connecting to Razorpay API: {str(exc)}",
                status_code=502
            )


razorpay_client = RazorpayClient()
