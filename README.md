# RecoverIQ — AI Revenue Recovery Agent for Razorpay

RecoverIQ is an AI-powered revenue recovery platform built for Razorpay merchants. It proactively monitors failed payments, expiring payment links, partial payments, and overdue invoices, evaluates recovery probabilities, applies deterministic safety policies, and automates revenue recovery.

> [!NOTE]
> **SYNTHETIC DATA STATEMENT**: All customer names, email addresses, phone numbers, transaction amounts, and payment events used during development and seeding are **100% synthetic**. No real customer data, live Razorpay credentials, or production API keys are used.

---

## 🏛️ High-Level Architecture

```
Razorpay Event (Failure / Expiring Link / Overdue)
                    ↓
         [Event Normalization]
                    ↓
     [Deterministic Recovery Scoring]
                    ↓
        [SQLite Persistence Layer]
                    ↓
 [FastAPI REST APIs (/metrics, /recovery-cases)]
                    ↓
 [Next.js Revenue Recovery Command Center]
```

### 🛡️ Safety-First Design Principle
- **The AI never executes financial actions directly.**
- All incoming events are normalized and evaluated through transparent deterministic heuristic rules before moving to execution pipelines.
- Stage 2 provides the persistent data model, event ingestion pipeline, and interactive dashboard.

---

## 💾 Database Architecture (SQLite / SQLAlchemy)

The database schema is designed for full PostgreSQL compatibility while running locally on SQLite:

1. **`customers`**:
   - `id`, `name`, `email`, `phone`, `total_transactions`, `successful_transactions`, `failed_transactions`, `total_paid` (in paise), `created_at`
2. **`payment_events`**:
   - `id`, `customer_id`, `event_type`, `amount` (in paise), `currency` (INR), `status`, `failure_reason`, `external_event_id`, `created_at`
3. **`recovery_cases`**:
   - `id`, `customer_id`, `payment_event_id`, `risk_score` (0–100), `recovery_probability` (0.0–1.0), `recommended_action`, `confidence`, `status` (`DETECTED`, `IN_PROGRESS`, `RECOVERED`), `created_at`
4. **`recovery_actions`**:
   - `id`, `recovery_case_id`, `action_type`, `status` (`PENDING`, `EXECUTED`, `FAILED`), `external_reference`, `created_at`

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status check |
| `GET` | `/api/dashboard/metrics` | Real-time aggregated KPIs (Revenue at risk, recovered volume, recovery rate) |
| `GET` | `/api/recovery-cases` | List all recovery cases with optional `?status=` filtering |
| `GET` | `/api/recovery-cases/{id}` | Detailed case diagnostics, customer profile, and scoring breakdown |
| `POST` | `/api/events` | Ingest and normalize raw payment events with automatic deduplication |
| `POST` | `/api/events/seed` | Reset SQLite DB and re-seed 14 synthetic customers and 25 payment events |

Interactive Swagger documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 🚀 Quick Start Guide

### 1. Backend Setup & Seeding

```bash
cd backend
python -m venv .venv

# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install dependencies:
pip install -r requirements.txt

# Reset and seed synthetic data:
python seed.py

# Start FastAPI server:
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the **Revenue Recovery Command Center**.
