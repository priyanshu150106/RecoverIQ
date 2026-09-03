from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.activity import ActivityItem
from app.services.activity_feed import activity_feed_service

router = APIRouter(tags=["Activity Feed & Case Timeline"])


@router.get(
    "/api/dashboard/activity-feed",
    response_model=List[ActivityItem],
    summary="Get Global Recovery Agent Activity Feed",
    description="Returns the most recent operational and AI activities across the platform, sorted newest first."
)
def get_dashboard_activity_feed(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of activities to return (default: 20, max: 100)"),
    db: Session = Depends(get_db)
) -> List[ActivityItem]:
    activities = activity_feed_service.get_global_activity_feed(db=db, limit=limit)
    return activities


@router.get(
    "/api/recovery-cases/{case_id}/timeline",
    response_model=List[ActivityItem],
    summary="Get Case Recovery Timeline",
    description="Returns the complete chronological lifecycle timeline for a specific recovery case, sorted oldest first."
)
def get_case_timeline(
    case_id: int,
    db: Session = Depends(get_db)
) -> List[ActivityItem]:
    timeline = activity_feed_service.get_case_timeline(db=db, case_id=case_id)
    if timeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case with ID {case_id} not found."
        )
    return timeline
