from fastapi import FastAPI

from app.config import settings
from app.logging_config import configure_logging
from app.metrics import metrics_response
from app.schemas import (
    ApiRolloutControlRequest,
    ApiRolloutEvaluationRequest,
    ApiRolloutHistoryRequest,
    PredictRequest,
)
from app.service import PredictionService

configure_logging()
app = FastAPI(title=settings.service_name)
service = PredictionService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/metrics")
def metrics():
    return metrics_response()


@app.post("/predict")
def predict(request: PredictRequest):
    return service.predict(request)


@app.post("/evaluate-rollout")
def evaluate_rollout(request: ApiRolloutEvaluationRequest):
    return service.evaluate_rollout(request)


@app.post("/rollout/evaluate")
def rollout_evaluate(request: ApiRolloutEvaluationRequest):
    return service.evaluate_rollout(request)


@app.post("/rollout/history")
def rollout_history(request: ApiRolloutHistoryRequest):
    return service.review_rollout_history(request)


@app.post("/rollout/control-review")
def rollout_control_review(request: ApiRolloutControlRequest):
    return service.review_rollout_control(request)
