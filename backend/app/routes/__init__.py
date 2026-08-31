"""API Route handlers for RecoverIQ."""
from app.routes.health import router as health_router
from app.routes.dashboard import router as dashboard_router
from app.routes.recovery_cases import router as recovery_cases_router
from app.routes.recovery_actions import router as recovery_actions_router
from app.routes.events import router as events_router

__all__ = [
    "health_router",
    "dashboard_router",
    "recovery_cases_router",
    "recovery_actions_router",
    "events_router",
]
