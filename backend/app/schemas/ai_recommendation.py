from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class AIRecoveryRecommendation(BaseModel):
    recovery_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated probability of successful revenue recovery between 0.0 and 1.0"
    )
    recommended_action: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Recommended operational recovery action"
    )
    urgency: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        ...,
        description="Execution urgency level based on failure time sensitivity"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the AI agent analysis between 0.0 and 1.0"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Concise diagnostic explanation of why this action was recommended"
    )
    signals: List[str] = Field(
        ...,
        min_items=1,
        description="Key behavioral, failure, and historical signals extracted from data"
    )
    policy_recommendation: Literal["ALLOW", "BLOCK", "REVIEW"] = Field(
        ...,
        description="Advisory policy suggestion (final authorization governed by deterministic policy engine)"
    )

    @field_validator("reasoning")
    @classmethod
    def validate_reasoning(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 10:
            raise ValueError("Reasoning must be at least 10 characters long.")
        return stripped


class AIRecoveryRecommendationResponse(BaseModel):
    status: str = "success"
    recovery_case_id: int
    source: Literal["ai", "fallback"] = Field(
        ...,
        description="Origin of the recommendation ('ai' for OpenAI LLM, 'fallback' for deterministic engine)"
    )
    model_used: Optional[str] = Field(None, description="OpenAI model identifier when source is 'ai'")
    recommendation: AIRecoveryRecommendation
