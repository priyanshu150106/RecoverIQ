from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.recovery_case import RecoveryCase
from app.schemas.ai_recommendation import AIRecoveryRecommendationResponse
from app.ai.recovery_agent import ai_recovery_agent

router = APIRouter(prefix="/api/recovery-cases", tags=["AI Recovery Agent"])


@router.post(
    "/{case_id}/ai-recommendation",
    response_model=AIRecoveryRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Recovery Recommendation",
    description="Analyzes payment failure, customer historical transactions, and risk signals via OpenAI (or deterministic fallback) without executing financial actions."
)
def get_ai_recovery_recommendation(
    case_id: int,
    db: Session = Depends(get_db)
):
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case with ID {case_id} not found."
        )

    recommendation_response = ai_recovery_agent.generate_recommendation(case=case)
    return recommendation_response
