# RecoverIQ — AI Revenue Recovery Agent for Razorpay

RecoverIQ is an AI-powered revenue recovery platform built for Razorpay merchants. It proactively monitors failed payments, expiring payment links, partial payments, and overdue invoices, evaluates recovery probabilities using AI models, enforces deterministic safety policies, and recovers lost revenue.

---

## 🏛️ High-Level Architecture

```
Razorpay Event (Failure / Expiring Link / Overdue)
                    ↓
         [Event Normalization]
                    ↓
       [Revenue Risk Engine (Heuristics)]
                    ↓
      [AI Recovery Agent (Structured Recommendations)]
                    ↓
   [Deterministic Policy Engine (Safety Gates)]
                    ↓
        [Human Approval OR Auto-Execution]
                    ↓
            [Razorpay Test API]
                    ↓
             [Audit Log & Analytics]
```

### 🛡️ Safety-First Design Principle
- **The AI never executes financial actions directly.**
- The AI only produces structured recommendations (`risk_score`, `recovery_probability`, `reason`, `recommended_action`, `confidence`, `requires_approval`).
- A **Deterministic Policy Engine** validates every action against merchant limits, cooldown windows, and safety rules before any call is made to Razorpay Test APIs.

---

## 📁 Repository Structure

```
recoveriq/
├── backend/                # Python FastAPI Backend
│   ├── app/
│   │   ├── ai/             # AI Recovery Agent & LLM Prompts
│   │   ├── models/         # SQLAlchemy DB Models
│   │   ├── policies/       # Deterministic Safety Policy Engine
│   │   ├── routes/         # FastAPI Route Handlers (Health, Events, Analytics)
│   │   ├── schemas/        # Pydantic Request & Response Schemas
│   │   ├── services/       # Business Logic & Normalization Services
│   │   ├── config.py       # Configuration & Environment Settings
│   │   ├── database.py     # Database Session & Base Engine
│   │   └── main.py         # Application Entrypoint & CORS Setup
│   └── requirements.txt    # Python Backend Dependencies
├── frontend/               # Next.js TypeScript Frontend
│   ├── src/
│   │   ├── app/            # App Router (Dashboard Pages & Layout)
│   │   └── components/     # UI Components & Metric Cards
│   └── package.json        # Frontend Dependencies & Scripts
├── docs/                   # System & Safety Architecture Documentation
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start (Development)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).
Health check available at [http://localhost:8000/health](http://localhost:8000/health).

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Dashboard will be available at [http://localhost:3000](http://localhost:3000).
