import os
from typing import List, Optional
from pydantic_settings import BaseSettings

# Absolute path to backend/.env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")


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

    # Razorpay Test Mode Credentials (loaded from backend/.env)
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None

    # Razorpay Webhook Secret (loaded from backend/.env)
    RECOVERIQ_WEBHOOK_SECRET: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ENV_FILE
        extra = "ignore"


settings = Settings()
