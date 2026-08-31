from pydantic import BaseModel, Field


class DashboardMetricsResponse(BaseModel):
    total_revenue_processed: int = Field(..., description="Total volume processed in paise")
    revenue_at_risk: int = Field(..., description="Unrecovered failed/expired payment volume in paise")
    recovery_rate: float = Field(..., description="Percentage of at-risk revenue successfully recovered")
    cases_detected: int = Field(..., description="Total count of payment risk cases identified")
    recovered_revenue: int = Field(..., description="Total recovered revenue in paise")
    potential_recovery: int = Field(..., description="Estimated recoverable amount based on probability weighting in paise")
    active_cases_count: int = Field(0, description="Number of currently active/unresolved recovery cases")
    recovered_cases_count: int = Field(0, description="Number of resolved/recovered cases")
