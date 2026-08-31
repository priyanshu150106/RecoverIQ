from pydantic import BaseModel, Field
from datetime import datetime


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Service health status", example="healthy")
    service: str = Field(..., description="Service identifier", example="RecoverIQ Backend")
    version: str = Field(..., description="Application version", example="0.1.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current UTC timestamp")
    environment: str = Field(..., description="Environment name", example="development")
