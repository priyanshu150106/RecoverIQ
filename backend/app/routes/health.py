from fastapi import APIRouter, status
from app.schemas.health import HealthCheckResponse
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns the current operational status of the RecoverIQ backend service."
)
def get_health() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT
    )
