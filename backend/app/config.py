from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "RecoverIQ"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # CORS Origins (Next.js frontend default port 3000)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    # Database configuration (SQLite for local rapid prototype)
    DATABASE_URL: str = "sqlite:///./recoveriq.db"

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
