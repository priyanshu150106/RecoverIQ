# RecoverIQ Architecture & Safety Specification

## 1. Stage 2 Data Pipeline Overview

```
Raw Ingestion (POST /api/events or Webhooks)
   │
   ▼
[EventNormalizer] ─── Standardizes to NormalizedEvent schema (Independent of gateway)
   │
   ▼
[EventIngestionService]
   ├── Deduplication Check (on external_event_id)
   ├── Customer Resolution (Find existing or create new Customer profile)
   ├── PaymentEvent Persistence (amount in paise, status, reason)
   │
   ▼ (if at-risk: payment.failed, payment_link.expired, etc.)
[RecoveryScorer] ──── Deterministic baseline heuristics (History, Amount, Failure Type)
   │
   ▼
[RecoveryCase & RecoveryAction Persistence]
   │
   ▼
[FastAPI Endpoints] ─ GET /api/dashboard/metrics & GET /api/recovery-cases
   │
   ▼
[Next.js Dashboard] ─ Live Recovery Queue, Metric Cards, Diagnostic Modals
```

## 2. Deterministic Baseline Scoring Heuristics

The Stage 2 scoring baseline uses transparent mathematical and rule-based evaluation:

1. **Failure Category Base Assessment**:
   - `Temporary Bank / Network Glitch` (e.g. `bank_authorization_timeout`): Risk: 28, Prob: 0.88, Action: `SEND_SMART_RETRY_LINK`
   - `Payment Link Expiry` (`payment_link_ttl_expired`): Risk: 42, Prob: 0.72, Action: `EXTEND_PAYMENT_LINK_24H`
   - `Partial Payment` (`payment_link.partially_paid`): Risk: 20, Prob: 0.92, Action: `SCHEDULE_WHATSAPP_REMINDER`
   - `Insufficient Balance`: Risk: 58, Prob: 0.58, Action: `FALLBACK_UPI_INTENT`
   - `Card Rejection` (`card_expired`, `card_declined`): Risk: 68, Prob: 0.45, Action: `SEND_UPDATE_PAYMENT_METHOD_LINK`
   - `Fraud / High Velocity Flag`: Risk: 92, Prob: 0.10, Action: `FLAG_MANUAL_REVIEW`

2. **Customer Historical Profile Adjustments**:
   - Loyal customer (>= 2 successes, >= 75% success rate): Risk -12, Prob +0.12
   - Repeat failure history (>= 2 failures, < 40% success rate): Risk +16, Prob -0.15

3. **Amount Bracket Modifiers**:
   - Low-ticket (< ₹1,500): Prob +0.05
   - High-ticket (> ₹20,000): Risk +8, Action: `OFFER_FLEXIBLE_PAYMENT_OPTION`

---

## 3. Synthetic Data Safeguard

All seed datasets and simulated events operate in isolation with zero external API calls to Razorpay or OpenAI in Stages 1 and 2.
