import uuid
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.database import engine, Base
import app.models  # Ensure all SQLAlchemy models are registered
from app.middleware.request_id import RequestIDMiddleware
from app.services.logging_service import structured_logger

from app.routes.health import router as health_router
from app.routes.dashboard import router as dashboard_router
from app.routes.recovery_cases import router as recovery_cases_router
from app.routes.recovery_actions import router as recovery_actions_router
from app.routes.webhooks import router as webhooks_router
from app.routes.events import router as events_router
from app.routes.ai_agent import router as ai_agent_router
from app.routes.activity import router as activity_router
from app.routes.demo import router as demo_router
from app.routes.strategy import router as strategy_router
from app.routes.recovery_approvals import router as recovery_approvals_router
from app.routes.analytics import router as analytics_router
from app.routes.system import router as system_router

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RecoverIQ — AI Revenue Recovery Agent for Razorpay Merchants (Backend API)"
)

# 1. Add Request ID Correlation Middleware
app.add_middleware(RequestIDMiddleware)

# 2. Configure Cross-Origin Resource Sharing (CORS) for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 3. Global Exception Handlers for Production Reliability
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    structured_logger.warning(
        component="api",
        operation=f"{request.method} {request.url.path}",
        message=str(exc.detail),
        request_id=request_id,
        details={"status_code": exc.status_code}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "detail": exc.detail,
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    structured_logger.warning(
        component="api_validation",
        operation=f"{request.method} {request.url.path}",
        message="Request payload validation failed",
        request_id=request_id,
        details={"errors": str(exc.errors())}
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "message": "Validation Error",
            "detail": exc.errors(),
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    structured_logger.error(
        component="unhandled_exception",
        operation=f"{request.method} {request.url.path}",
        message="An unexpected server error occurred",
        request_id=request_id,
        details={"exception_type": type(exc).__name__}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "An internal server error occurred. Please contact support referencing request_id.",
            "detail": "Internal server error",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id}
    )


# 4. Register Route Modules
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(recovery_cases_router)
app.include_router(recovery_actions_router)
app.include_router(webhooks_router)
app.include_router(events_router)
app.include_router(ai_agent_router)
app.include_router(activity_router)
app.include_router(demo_router)
app.include_router(strategy_router)
app.include_router(recovery_approvals_router)
app.include_router(analytics_router)
app.include_router(system_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "readiness": "/api/system/readiness",
            "system_metrics": "/api/system/metrics",
            "dashboard_metrics": "/api/dashboard/metrics",
            "analytics_overview": "/api/analytics/overview",
            "analytics_strategies": "/api/analytics/strategies",
            "analytics_trend": "/api/analytics/recovery-trend",
            "activity_feed": "/api/dashboard/activity-feed",
            "recovery_cases": "/api/recovery-cases",
            "case_timeline": "/api/recovery-cases/{case_id}/timeline",
            "execute_link": "/api/recovery-cases/{case_id}/execute-link",
            "ai_recommendation": "/api/recovery-cases/{case_id}/ai-recommendation",
            "strategy": "/api/recovery-cases/{case_id}/strategy",
            "approvals": "/api/recovery-cases/{case_id}/approval",
            "demo_simulate_payment": "/api/demo/recovery/{case_id}/simulate-payment",
            "webhooks": "/api/webhooks/razorpay",
            "events_ingestion": "/api/events"
        }
    }
