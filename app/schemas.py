from pydantic import BaseModel, Field

from model_serving_canary_platform.models import (
    PredictionFeatures,
    RolloutControlRequest,
    RolloutEvaluationRequest,
    RolloutHistoryRequest,
)


class PredictRequest(PredictionFeatures):
    canary_percent: int | None = Field(default=None, ge=0, le=100)


class PredictResponse(BaseModel):
    selected_model: str
    canary_percent: int
    risk_score: float
    priority: str
    baseline_risk_score: float
    canary_risk_score: float
    priority_changed: bool
    route_reason: str


class ApiRolloutEvaluationRequest(RolloutEvaluationRequest):
    pass


class ApiRolloutHistoryRequest(RolloutHistoryRequest):
    pass


class ApiRolloutControlRequest(RolloutControlRequest):
    pass
