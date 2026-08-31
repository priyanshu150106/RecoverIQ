from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db, Base, engine
from app.schemas.event import EventIngestionResponse
from app.services.event_ingestion import event_ingestion_service

router = APIRouter(prefix="/api/events", tags=["Events"])


@router.post(
    "",
    response_model=EventIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Raw Payment Event",
    description="Accepts a raw payment or link event, normalizes it, and triggers recovery workflow if at risk."
)
def ingest_event(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
) -> EventIngestionResponse:
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload body must not be empty."
        )
    return event_ingestion_service.ingest_raw_event(db=db, raw_payload=payload)


@router.post(
    "/seed",
    summary="Seed Synthetic Data",
    description="Resets the database and populates it with synthetic customers, events, and recovery cases."
)
def seed_synthetic_data(db: Session = Depends(get_db)):
    from seed import run_seed
    result = run_seed()
    return {
        "status": "success",
        "message": "Database reset and seeded with synthetic data.",
        "details": result
    }
