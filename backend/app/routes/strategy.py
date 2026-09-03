from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.recovery_case import RecoveryCase
from app.schemas.recovery_strategy import RecoveryStrategyResponse
from app.services.recovery_strategy import recovery_strategy_engine

router = APIRouter(prefix="/api/recovery-cases", tags=["Recovery Strategy"])


@router.post(
    "/{case_id}/strategy",
    response_model=RecoveryStrategyResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Deterministic Recovery Strategy",
    description="Evaluates diagnostic heuristics against deterministic policy rules to recommend the safest recovery strategy without executing financial actions."
)
def evaluate_recovery_strategy(
    case_id: int,
    db: Session = Depends(get_db)
) -> RecoveryStrategyResponse:
    case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery case with ID {case_id} not found."
        )

    strategy_response = recovery_strategy_engine.evaluate(case=case)
    return strategy_response
