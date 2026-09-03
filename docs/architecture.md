# RecoverIQ Architecture & Safety Specification

## 1. End-to-End Recovery Pipeline (Stages 1–7)

```
Payment Failure / Expiring Link / Webhook
                     │
                     ▼
         [EventNormalizer] ────────── Standardizes to NormalizedEvent schema
                     │
                     ▼
       [EventIngestionService]
          ├── Deduplication Check (on external_event_id)
          ├── Customer Profile Resolution
          └── PaymentEvent Persistence
                     │
                     ▼
        [RecoveryScorer] ──────────── Deterministic baseline risk & probability
                     │
                     ▼
        [RecoveryCase Created] ────── Status: DETECTED
                     │
                     ▼
     [OpenAI Recovery Agent] ──────── Consultative Diagnostic Analysis
          └── Signals, Urgency, Failure Root Cause (Zero PII transmitted)
                     │
                     ▼
   [Recovery Strategy Engine] ─────── Deterministic Rule Matrix
          ├── SEND_SMART_RETRY_LINK
          ├── SEND_PAYMENT_LINK
          ├── SEND_REMINDER
          ├── HUMAN_REVIEW
          └── NO_ACTION
                     │
                     ▼
   [Human-in-the-Loop Console] ────── Status: PENDING ➔ APPROVED / REJECTED
                     │
                     ▼ (If Approved)
    [Deterministic Policy Gate] ───── Fresh re-check (rzp_test_, cap <= ₹50,000, 30m cooldown)
                     │
                     ▼
    [Razorpay Test Execution] ─────── Dispatches payment link to Razorpay sandbox
                     │
                     ▼
     [Razorpay Webhook Receiver] ──── HMAC-SHA256 verification + idempotency
          ├── payment_link.paid ────────── Status: RECOVERED
          ├── payment_link.partially_paid ─ Status: IN_PROGRESS
          ├── payment_link.cancelled ───── Status: CANCELLED
          └── payment_link.expired ─────── Status: EXPIRED
                     │
                     ▼
   [Recovery Outcome & Analytics] ─── Verified financial tracking & strategy matrix
```

---

## 2. Core Architectural Principles: Prediction ≠ Execution ≠ Outcome

RecoverIQ maintains strict architectural boundaries:

| Phase | Subsystem | Responsibility | Invariant |
|---|---|---|---|
| **Prediction** | OpenAI Agent & Baseline Scorer | Diagnostic analysis and probability estimation | **Consultative Only** — Cannot trigger financial operations. |
| **Strategy** | Recovery Strategy Engine | Deterministic routing based on risk and failure type | Enforces operator review for high-risk or ambiguous cases. |
| **Authorization** | Approval Service | Operator approval workflow | Every execution requires a fresh safety gate validation. |
| **Execution** | Razorpay Client | Generates test payment links | **Test Mode Only** (`rzp_test_`), ₹50k cap, 30-min cooldown. |
| **Outcome** | Recovery Outcome Service | Reconciles actual revenue recovered and duration | **Empirical Only** — Derived from cryptographic webhooks. |

---

## 3. Reliability, Observability & Error Handling

- **`X-Request-ID`**: Propagated across every HTTP request and logged for end-to-end tracing.
- **Structured JSON Logging**: Masked and sanitized log entries with zero secrets, webhook tokens, or customer PII.
- **Transactional Webhook Processing**: Atomic database commits with automatic rollback on error.
- **Readiness Probes**: `/api/system/readiness` and `/api/system/metrics` endpoints for health monitoring.
- **Fail-Safe Fallback**: Deterministic rule engines remain fully operational even if external AI or network providers are degraded.
