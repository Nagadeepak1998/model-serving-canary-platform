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


class RolloutHistoryWindow(BaseModel):
    observed_at: str
    stage_started_at: str | None = None
    max_stage_age_minutes: int = Field(default=30, ge=1)
    evaluation: RolloutEvaluationRequest
    rollback: "RollbackCompletionEvidence | None" = None


class RollbackCompletionEvidence(BaseModel):
    completed_at: str
    owner: str = Field(min_length=3)
    evidence_url: str = Field(min_length=8)


class RolloutHistoryRequest(BaseModel):
    windows: list[RolloutHistoryWindow] = Field(min_length=2)
    max_non_promote_windows: int = Field(default=1, ge=0)


class RolloutHistoryWindowResult(BaseModel):
    observed_at: str
    decision: str
    canary_percent: int
    priority_mismatch_rate: float
    average_score_delta: float
    stage_age_minutes: int | None
    stale: bool


class RolloutHistoryReport(BaseModel):
    decision: str
    reviewed_windows: int
    non_promote_windows: int
    rollback_windows: int
    stale_windows: int
    latest_decision: str
    rollback_completion: str
    rollback_evidence_complete: bool
    reasons: list[str]
    windows: list[RolloutHistoryWindowResult]


class RolloutStageEvidence(BaseModel):
    canary_percent: int = Field(ge=0, le=100)
    started_at: str
    completed_at: str | None = None
    decision: str
    evidence_uri: str = Field(min_length=1)


class RolloutApproval(BaseModel):
    requested_by: str = Field(min_length=1)
    approved_by: str = Field(min_length=1)
    approved_at: str


class RollbackEvidence(BaseModel):
    required: bool = False
    completed_at: str | None = None
    restored_model: str | None = None
    evidence_uri: str | None = None


class RolloutControlRequest(BaseModel):
    release_id: str = Field(min_length=1)
    baseline_model: str = Field(min_length=1)
    canary_model: str = Field(min_length=1)
    reference_time: str
    approval_max_age_minutes: int = Field(default=60, ge=1)
    approval: RolloutApproval
    stages: list[RolloutStageEvidence] = Field(min_length=1)
    rollback: RollbackEvidence = Field(default_factory=RollbackEvidence)


class RolloutControlReport(BaseModel):
    decision: str
    release_id: str
    reviewed_stages: int
    latest_canary_percent: int
    approval_age_minutes: int
    rollback_required: bool
    rollback_complete: bool
    findings: list[str]
