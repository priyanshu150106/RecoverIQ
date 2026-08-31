# RecoverIQ Architecture & Safety Specification

## 1. System Pipeline Overview

RecoverIQ processes revenue leakages through an 8-stage pipeline:

```
1. Razorpay Event Ingestion (Webhooks / Test APIs)
   │
2. Event Normalization
   │ - Maps heterogeneous Razorpay payloads into unified RecoverIQ Event schemas
   │
3. Revenue Risk Engine
   │ - Assesses risk magnitude, merchant exposure, customer payment history
   │
4. AI Recovery Agent
   │ - Evaluates root failure causes (e.g., card expiry, bank downtime, auth timeout)
   │ - Generates structured recommendations (NEVER executes actions directly)
   │
5. Deterministic Policy Engine
   │ - Validates recovery action against strict hard limits:
   │   • Max discount limits
   │   • Cooldown periods between retries
   │   • Maximum automated value threshold
   │   • Blacklists and merchant preferences
   │
6. Execution Gate (Human Approval vs. Safe Auto-Execution)
   │ - High-risk or low-confidence actions require human merchant approval
   │ - Low-risk policy-compliant actions are approved for auto-execution
   │
7. Razorpay Test API Execution
   │ - Dispatches approved recovery payload (e.g. regenerative payment link, smart retry)
   │
8. Audit Trail & Real-Time Analytics
   │ - Persists immutable log of event, AI reasoning, policy checks, and execution outcome
```

## 2. Structured AI Recommendation Schema

The AI Agent is strictly confined to outputting JSON adhering to this structure:

```json
{
  "event_id": "evt_123456",
  "risk_score": 0.85,
  "recovery_probability": 0.72,
  "reason": "Customer payment failed due to issuing bank 3DS timeout on credit card.",
  "recommended_action": "SEND_RETRY_LINK_WITH_UPI_ALTERNATIVE",
  "confidence": 0.91,
  "requires_approval": false,
  "action_payload": {
    "expiry_hours": 24,
    "suggest_alternative_payment_method": "upi"
  }
}
```

## 3. Deterministic Safety Policies

Policies override the AI in all circumstances:
- **Maximum Retries**: No customer is contacted more than 3 times for a single invoice.
- **Value Safeguard**: Any recovery action with monetary impact > ₹50,000 requires explicit human approval.
- **Cooldown Window**: Minimum 6 hours between automated reminders.
- **Test Mode Isolation**: In development, all actions strictly target Razorpay Test Mode.
