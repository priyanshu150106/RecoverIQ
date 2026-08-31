from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
import app.models  # Ensure all SQLAlchemy models are registered
from app.routes.health import router as health_router
from app.routes.dashboard import router as dashboard_router
from app.routes.recovery_cases import router as recovery_cases_router
from app.routes.events import router as events_router

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RecoverIQ — AI Revenue Recovery Agent for Razorpay Merchants (Backend API)"
)

# Configure Cross-Origin Resource Sharing (CORS) for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(recovery_cases_router)
app.include_router(events_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "dashboard_metrics": "/api/dashboard/metrics",
            "recovery_cases": "/api/recovery-cases",
            "events_ingestion": "/api/events"
        }
    }
