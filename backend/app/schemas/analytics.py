from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field

OutcomeStatus = Literal[
    "RECOVERED",
    "PARTIALLY_RECOVERED",
    "FAILED",
    "EXPIRED",
    "CANCELLED",
    "PENDING",
]


class RecoveryOutcomeResponse(BaseModel):
    id: int = Field(..., description="Outcome record ID")
    recovery_case_id: int = Field(..., description="Target RecoveryCase ID")
    recovery_action_id: Optional[int] = Field(None, description="Associated RecoveryAction ID if applicable")
    strategy_type: str = Field(..., description="Recovery strategy executed")
    outcome_status: OutcomeStatus = Field(..., description="Measurable outcome state")
    amount_at_risk: int = Field(..., description="Initial amount at risk in paise")
    amount_recovered: int = Field(..., description="Actual amount recovered in paise")
    recovery_percentage: float = Field(..., description="Percentage of amount recovered (0-100%)")
    execution_timestamp: datetime = Field(..., description="UTC execution timestamp")
    recovery_timestamp: Optional[datetime] = Field(None, description="UTC recovery timestamp")
    time_to_recovery_seconds: Optional[float] = Field(None, description="Elapsed seconds between execution and recovery")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class AnalyticsOverviewResponse(BaseModel):
    revenue_at_risk: int = Field(..., description="Total revenue currently or historically at risk (paise)")
    revenue_recovered: int = Field(..., description="Total actual revenue recovered (paise)")
    recovery_rate: float = Field(..., description="Aggregate recovery success percentage (0-100%)")
    average_recovery_percentage: float = Field(..., description="Mean recovery percentage across all executed cases")
    average_time_to_recovery_seconds: float = Field(..., description="Average recovery duration in seconds")
    executed_actions: int = Field(..., description="Total count of executed recovery attempts")
    successful_recoveries: int = Field(..., description="Total count of fully recovered cases")
    partial_recoveries: int = Field(..., description="Total count of partially recovered cases")
    failed_recoveries: int = Field(..., description="Total count of failed recovery actions")
    expired_recoveries: int = Field(..., description="Total count of expired links")
    cancelled_recoveries: int = Field(..., description="Total count of cancelled recovery attempts")
    pending_recoveries: int = Field(..., description="Total count of pending/active recovery attempts")


class StrategyAnalyticsResponse(BaseModel):
    strategy: str = Field(..., description="Recovery strategy name")
    cases: int = Field(..., description="Total cases routed to this strategy")
    executions: int = Field(..., description="Total executions for this strategy")
    recovered_cases: int = Field(..., description="Fully recovered cases")
    partial_recoveries: int = Field(..., description="Partially recovered cases")
    failed_cases: int = Field(..., description="Failed executions")
    recovery_rate: float = Field(..., description="Percentage of executions that succeeded (0-100%)")
    amount_at_risk: int = Field(..., description="Total volume at risk for this strategy (paise)")
    amount_recovered: int = Field(..., description="Total volume recovered by this strategy (paise)")
    average_recovery_time: float = Field(..., description="Average seconds to recover for this strategy")


class RecoveryTrendPoint(BaseModel):
    date: str = Field(..., description="ISO Date string (YYYY-MM-DD)")
    amount_at_risk: int = Field(..., description="Revenue at risk volume on this day (paise)")
    amount_recovered: int = Field(..., description="Revenue recovered volume on this day (paise)")
    recovery_rate: float = Field(..., description="Recovery percentage on this day (0-100%)")


class AIPerformanceResponse(BaseModel):
    analyzed_cases: int = Field(..., description="Total cases evaluated by AI Agent")
    recovered_cases: int = Field(..., description="Count of AI-analyzed cases successfully recovered")
    average_predicted_probability: float = Field(..., description="Mean AI predicted recovery probability (0-1)")
    average_actual_recovery_percentage: float = Field(..., description="Mean actual recovery percentage (0-100%)")
    prediction_gap: float = Field(..., description="Accuracy metric: absolute gap between prediction and actual outcome")
