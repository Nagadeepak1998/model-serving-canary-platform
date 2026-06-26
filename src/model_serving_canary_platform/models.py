from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionFeatures(BaseModel):
    ticket_id: str = Field(min_length=3)
    account_tier: str
    minutes_open: int = Field(ge=0)
    message_length: int = Field(ge=1)
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    similar_incidents: int = Field(ge=0)
    escalation_keywords: int = Field(ge=0)


class PredictionResult(BaseModel):
    model: str
    risk_score: float = Field(ge=0.0, le=1.0)
    priority: str
    summary: str


class ReleaseDecision(BaseModel):
    selected_model: str
    canary_percent: int = Field(ge=0, le=100)
    reason: str


class ShadowComparison(BaseModel):
    absolute_score_delta: float = Field(ge=0.0, le=1.0)
    priority_changed: bool
    baseline_priority: str
    canary_priority: str


class RolloutEvaluationCase(PredictionFeatures):
    expected_priority: str | None = None


class RolloutEvaluationRequest(BaseModel):
    canary_percent: int = Field(ge=0, le=100)
    max_priority_mismatch_rate: float = Field(default=0.2, ge=0.0, le=1.0)
    max_average_score_delta: float = Field(default=0.12, ge=0.0, le=1.0)
    cases: list[RolloutEvaluationCase] = Field(min_length=1)


class RolloutEvaluationCaseResult(BaseModel):
    ticket_id: str
    baseline_priority: str
    canary_priority: str
    score_delta: float
    priority_changed: bool
    expected_priority: str | None
    expected_priority_matched: bool | None


class RolloutEvaluationReport(BaseModel):
    decision: str
    canary_percent: int
    case_count: int
    priority_mismatch_rate: float
    average_score_delta: float
    max_score_delta: float
    expected_priority_miss_rate: float | None
    reasons: list[str]
    cases: list[RolloutEvaluationCaseResult]
