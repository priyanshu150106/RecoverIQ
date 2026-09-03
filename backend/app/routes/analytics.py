from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    StrategyAnalyticsResponse,
    RecoveryTrendPoint,
    RecoveryOutcomeResponse,
    AIPerformanceResponse,
)
from app.services.recovery_analytics import recovery_analytics_service

router = APIRouter(prefix="/api/analytics", tags=["Recovery Analytics & Intelligence"])


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Recovery Portfolio Overview Analytics",
    description="Returns aggregate revenue recovery, rate, duration, and execution volume metrics."
)
def get_analytics_overview(
    db: Session = Depends(get_db)
) -> AnalyticsOverviewResponse:
    return recovery_analytics_service.get_analytics_overview(db=db)


@router.get(
    "/strategies",
    response_model=List[StrategyAnalyticsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Strategy-Level Performance Analytics",
    description="Returns performance breakdown for each deterministic recovery strategy."
)
def get_strategy_analytics(
    db: Session = Depends(get_db)
) -> List[StrategyAnalyticsResponse]:
    return recovery_analytics_service.get_strategy_analytics(db=db)


@router.get(
    "/recovery-trend",
    response_model=List[RecoveryTrendPoint],
    status_code=status.HTTP_200_OK,
    summary="Get Recovery Volume & Rate Trend",
    description="Returns time-series daily volume at risk and recovery amounts for charting."
)
def get_recovery_trend(
    days: int = Query(7, ge=1, le=90, description="Number of days for trend aggregation"),
    db: Session = Depends(get_db)
) -> List[RecoveryTrendPoint]:
    return recovery_analytics_service.get_recovery_trend(db=db, days=days)


@router.get(
    "/cases/{case_id}",
    response_model=RecoveryOutcomeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Recovery Outcome for Case",
    description="Returns measurable outcome record and time to recovery for a specific case."
)
def get_case_outcome(
    case_id: int,
    db: Session = Depends(get_db)
) -> RecoveryOutcomeResponse:
    outcome = recovery_analytics_service.get_case_outcome(db=db, case_id=case_id)
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case with ID {case_id} not found."
        )
    return outcome


@router.get(
    "/ai-performance",
    response_model=AIPerformanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get AI Diagnosis vs Actual Recovery Outcome Analytics",
    description="Measures AI diagnosis accuracy and correlation with verified recovery outcomes."
)
def get_ai_performance(
    db: Session = Depends(get_db)
) -> AIPerformanceResponse:
    return recovery_analytics_service.get_ai_performance(db=db)
