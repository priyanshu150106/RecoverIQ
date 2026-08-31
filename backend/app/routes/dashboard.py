from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.payment_event import PaymentEvent
from app.models.recovery_case import RecoveryCase
from app.schemas.metrics import DashboardMetricsResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get(
    "/metrics",
    response_model=DashboardMetricsResponse,
    summary="Get Aggregated Dashboard Metrics",
    description="Calculates live revenue recovery KPIs from the database."
)
def get_dashboard_metrics(db: Session = Depends(get_db)) -> DashboardMetricsResponse:
    # Total volume processed
    total_revenue_processed = db.query(func.coalesce(func.sum(PaymentEvent.amount), 0)).scalar()

    # Recovery cases
    all_cases = db.query(RecoveryCase).join(PaymentEvent).all()
    cases_detected = len(all_cases)

    revenue_at_risk = 0
    recovered_revenue = 0
    potential_recovery = 0
    active_cases_count = 0
    recovered_cases_count = 0

    for case in all_cases:
        amt = case.payment_event.amount if case.payment_event else 0
        if case.status in ("DETECTED", "IN_PROGRESS"):
            revenue_at_risk += amt
            potential_recovery += int(amt * case.recovery_probability)
            active_cases_count += 1
        elif case.status == "RECOVERED":
            recovered_revenue += amt
            recovered_cases_count += 1

    # Recovery rate percentage
    total_risk_pool = recovered_revenue + revenue_at_risk
    if total_risk_pool > 0:
        recovery_rate = round((recovered_revenue / total_risk_pool) * 100.0, 1)
    else:
        recovery_rate = 0.0

    return DashboardMetricsResponse(
        total_revenue_processed=int(total_revenue_processed),
        revenue_at_risk=revenue_at_risk,
        recovery_rate=recovery_rate,
        cases_detected=cases_detected,
        recovered_revenue=recovered_revenue,
        potential_recovery=potential_recovery,
        active_cases_count=active_cases_count,
        recovered_cases_count=recovered_cases_count
    )
