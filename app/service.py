from __future__ import annotations

import logging
from time import perf_counter

from app.config import settings
from app.metrics import (
    prediction_latency_seconds,
    prediction_requests_total,
    shadow_priority_mismatch_total,
)
from app.schemas import PredictRequest, PredictResponse
from model_serving_canary_platform.inference import baseline_predict, canary_predict
from model_serving_canary_platform.rollout import CanaryRouter
from model_serving_canary_platform.shadow import ShadowComparator

logger = logging.getLogger(__name__)


class PredictionService:
    def __init__(self) -> None:
        self.router = CanaryRouter(
            baseline_model=settings.baseline_model_name,
            canary_model=settings.canary_model_name,
        )
        self.shadow = ShadowComparator()

    def predict(self, request: PredictRequest) -> PredictResponse:
        canary_percent = request.canary_percent
        if canary_percent is None:
            canary_percent = settings.default_canary_percent

        started = perf_counter()
        decision = self.router.decide(request.ticket_id, canary_percent)
        baseline_result = baseline_predict(request, settings.baseline_model_name)
        canary_result = canary_predict(request, settings.canary_model_name)
        selected_result = (
            canary_result
            if decision.selected_model == settings.canary_model_name
            else baseline_result
        )
        shadow_result = self.shadow.compare(baseline_result, canary_result)

        if shadow_result.priority_changed:
            shadow_priority_mismatch_total.inc()

        prediction_requests_total.labels(selected_model=selected_result.model).inc()
        prediction_latency_seconds.observe(perf_counter() - started)

        logger.info(
            "ticket_id=%s selected_model=%s canary_percent=%s risk_score=%s priority=%s",
            request.ticket_id,
            selected_result.model,
            canary_percent,
            selected_result.risk_score,
            selected_result.priority,
        )

        return PredictResponse(
            selected_model=selected_result.model,
            canary_percent=canary_percent,
            risk_score=selected_result.risk_score,
            priority=selected_result.priority,
            baseline_risk_score=baseline_result.risk_score,
            canary_risk_score=canary_result.risk_score,
            priority_changed=shadow_result.priority_changed,
            route_reason=decision.reason,
        )
