# RecoverIQ — AI Revenue Recovery Agent for Razorpay

RecoverIQ is an autonomous revenue recovery and intelligence platform built for Razorpay merchants. It proactively detects payment failures, expiring payment links, partial payments, and overdue invoices, generates AI and deterministic diagnostic strategies, enforces human-in-the-loop approvals, executes Razorpay Test Mode recovery links, and reconciles actual recovery outcomes through auditable analytics.

> [!NOTE]
> **SYNTHETIC DATA STATEMENT**: All customer names, email addresses, phone numbers, transaction amounts, and payment events used during development and seeding are **100% synthetic**. No real customer data, live Razorpay credentials, or production API keys are used.

---

## 🏛️ System Architecture (Stages 1–7)

```
Payment Failure / Webhook / Ingestion Event
                     ↓
         [Event Normalization & Deduplication]
                     ↓
       [Deterministic Baseline Risk Scorer]
                     ↓
      [OpenAI Recovery Agent (gpt-4o-mini)]
        └── Structured JSON Diagnostic Reasoning (Zero PII sent)
                     ↓
     [Deterministic Recovery Strategy Engine]
        ├── SEND_SMART_RETRY_LINK
        ├── SEND_PAYMENT_LINK
        ├── SEND_REMINDER
        ├── HUMAN_REVIEW
        └── NO_ACTION
                     ↓
      [Human-in-the-Loop Approval Console]
        ├── Explicit Operator Authorization (APPROVE / REJECT)
        └── Re-verifies Hard Policy Gates before Execution
                     ↓
    [Razorpay Test Mode Execution Client]
        ├── Prefix Isolation ('rzp_test_')
        ├── ₹50,000 Safety Cap
        └── 30-Minute Anti-Spam Cooldown
                     ↓
   [Cryptographic HMAC Webhook Processor]
        ├── X-Razorpay-Event-Id Deduplication
        └── Transactional Rollback Safety
                     ↓
     [Measurable Outcome Tracking & Analytics]
        ├── PREDICTION ≠ EXECUTION ≠ OUTCOME Separation
        ├── Strategy Efficiency Matrix
        ├── AI Calibration & Prediction Gap Analysis
        └── Real-Time Activity & Case Timelines
```

---

## 🛡️ Core Security & Deterministic Safety Guarantees

1. **AI Never Directly Executes Financial Actions**: The OpenAI agent is strictly consultative. Execution always flows through deterministic policy gates and human approvals.
2. **Test Mode Prefix Isolation**: Only Razorpay keys starting with `rzp_test_` can execute. Live mode keys (`rzp_live_`) are blocked at the code level.
3. **Hard Transaction Cap**: Single recovery links exceeding ₹50,000 (5,000,000 paise) are blocked automatically.
4. **Anti-Spam Cooldown**: 30-minute cooldown window prevents duplicate links from bombarding customers.
5. **HMAC-SHA256 Webhook Verification**: All webhook payloads are cryptographically validated over raw HTTP request bytes using `hmac.compare_digest` before parsing.
6. **Correlation & Request IDs**: Every request receives a unique `X-Request-ID` UUID for full auditability.
7. **PII & Secret Sanitization**: Zero API keys, webhook secrets, customer emails, or phone numbers are ever logged or sent to LLM prompts.
8. **Development Sandbox Resilience**: In local development, if external sandbox API authentication fails, a deterministic simulated test link (`plink_test_dev_...`) is generated so local tests and evaluations operate smoothly without live dependencies.

---

## 💾 Database Architecture (SQLite / SQLAlchemy)

1. **`customers`**: Profiles with transactional velocity and lifetime spend in paise.
2. **`payment_events`**: Normalized event history with external event ID deduplication.
3. **`recovery_cases`**: Core state machine (`DETECTED`, `IN_PROGRESS`, `RECOVERED`, `CANCELLED`, `EXPIRED`).
4. **`recovery_actions`**: Auditable execution records linking to Razorpay test payment links.
5. **`recovery_approvals`**: Operator authorization records (`PENDING`, `APPROVED`, `REJECTED`, `EXECUTED`).
6. **`recovery_outcomes`**: Verified financial reconciliation records tracking actual revenue recovered and elapsed duration.

---

## 🌐 Complete API Specification

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Lightweight service health liveness check |
| `GET` | `/api/system/readiness` | Subsystem readiness (DB, Razorpay Test, OpenAI, Webhook) |
| `GET` | `/api/system/metrics` | System-level operational counters and execution metrics |
| `GET` | `/api/dashboard/metrics` | Executive KPIs (Revenue at risk, recovered volume, rate) |
| `GET` | `/api/dashboard/activity-feed` | Chronological activity feed with actor metadata |
| `GET` | `/api/recovery-cases` | List recovery cases with status filters |
| `GET` | `/api/recovery-cases/{id}` | Detailed case diagnostics and customer profiles |
| `GET` | `/api/recovery-cases/{id}/timeline` | Chronological recovery lifecycle event stream |
| `POST` | `/api/recovery-cases/{id}/ai-recommendation` | OpenAI diagnostic failure analysis and recovery probability |
| `POST` | `/api/recovery-cases/{id}/strategy` | Deterministic strategy engine recommendation |
| `POST` | `/api/recovery-cases/{id}/approval` | Request human approval for strategy execution |
| `GET` | `/api/approvals/pending` | List pending approval queue |
| `POST` | `/api/approvals/{id}/approve` | Approve strategy with audit trail |
| `POST` | `/api/approvals/{id}/reject` | Reject strategy with operator reason |
| `POST` | `/api/approvals/{id}/execute` | Safely execute approved strategy to Razorpay Test Mode |
| `POST` | `/api/recovery-cases/{id}/execute-link` | Direct payment link generation (legacy endpoint) |
| `GET` | `/api/analytics/overview` | Executive portfolio outcome analytics |
| `GET` | `/api/analytics/strategies` | Strategy efficiency matrix across all 5 strategies |
| `GET` | `/api/analytics/recovery-trend` | Time-series volume at risk vs recovered for charting |
| `GET` | `/api/analytics/cases/{case_id}` | Case outcome and time to recovery details |
| `GET` | `/api/analytics/ai-performance` | AI prediction accuracy vs actual recovery reconciliation |
| `POST` | `/api/webhooks/razorpay` | Cryptographically verified webhook receiver |
| `POST` | `/api/events` | Ingest and normalize payment events |
| `POST` | `/api/events/seed` | Reset and re-seed synthetic customers and payment events |

Interactive Swagger documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 🚀 Quick Start Guide

### 1. Environment Configuration

Create `backend/.env` (untracked, never committed):

```bash
PROJECT_NAME=RecoverIQ
VERSION=0.8.0
ENVIRONMENT=development
DATABASE_URL=sqlite:///./recoveriq.db

# Razorpay Test Mode Credentials (Prefix MUST be rzp_test_)
RAZORPAY_KEY_ID=rzp_test_YOUR_KEY_ID
RAZORPAY_KEY_SECRET=YOUR_KEY_SECRET
RECOVERIQ_WEBHOOK_SECRET=your_webhook_secret_here

# OpenAI API Key (Optional — graceful fallback engine is active if unset)
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Backend Setup & Startup

```bash
cd backend
python -m venv .venv

# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install dependencies:
pip install -r requirements.txt

# Seed synthetic database records & recovery outcomes:
python seed.py

# Start FastAPI server:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup & Startup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the **Revenue Recovery Command Center**.

---

## 🧪 Automated Regression Testing

To run the complete 8-suite regression battery:

```bash
cd backend

# Reset database to clean synthetic state:
.venv\Scripts\python seed.py

# Run all test suites:
.venv\Scripts\python test_api.py
.venv\Scripts\python test_stage3.py
.venv\Scripts\python test_webhooks.py
.venv\Scripts\python test_ai_agent.py
.venv\Scripts\python test_stage5_activity.py
.venv\Scripts\python test_recovery_strategy.py
.venv\Scripts\python test_recovery_approvals.py
.venv\Scripts\python test_stage7_analytics.py
```

To run the production frontend build:

```bash
cd frontend
npm run build
```

---

## 🎬 Presentation Demo Workflow

1. **Dashboard Overview**: Open [http://localhost:3000](http://localhost:3000). Inspect the 4 core KPI metrics: *Revenue at Risk*, *Recovery Rate*, *Cases Detected*, and *Recovered Revenue*.
2. **System Health**: Review the *System Observability & Reliability* widget confirming database, Razorpay test mode, webhook, and AI status.
3. **Select a Case**: Click on an active case (e.g. Case #2 or Case #4) in the *Recovery Queue*.
4. **Inspect Deterministic Score**: Review the risk score (0-100), recovery probability, and root cause classification.
5. **Run AI Agent**: Click *Run AI Diagnostic Analysis*. Review the structured JSON output (urgency, confidence, signals, and reasoning) with zero PII exposure.
6. **Evaluate Strategy**: View the recommended deterministic strategy (e.g. `SEND_SMART_RETRY_LINK`).
7. **Request Approval**: Click *Request Operator Approval*. Observe the case status transition and activity feed entry.
8. **Approve Action**: Switch to the approver role and click *Approve Strategy*.
9. **Controlled Execution**: Click *Execute Approved Action*. The system re-checks all 4 hard policy gates and creates a Razorpay Test Mode payment link.
10. **Timeline Audit**: Observe the chronological lifecycle milestones in the case timeline.
11. **Simulate Webhook**: Ingest a simulated `payment_link.paid` webhook. Notice the case transitioning to `RECOVERED` and the financial reconciliation reflected in *Recovery Analytics*.
12. **Verify Idempotency**: Resend the same webhook. Confirm it is safely ignored as a duplicate (`status: ignored`) without double-crediting.
