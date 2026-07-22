from __future__ import annotations

import logging
from time import perf_counter

from app.config import settings
from app.metrics import (
    prediction_latency_seconds,
    prediction_requests_total,
    rollout_average_score_delta,
    rollout_control_reviews_total,
    rollout_evaluations_total,
    rollout_history_reviews_total,
    rollout_priority_mismatch_rate,
    rollout_rollback_evidence_complete,
    rollout_stale_windows,
    shadow_priority_mismatch_total,
)
from app.schemas import (
    ApiRolloutControlRequest,
    ApiRolloutEvaluationRequest,
    ApiRolloutHistoryRequest,
    PredictRequest,
    PredictResponse,
)
from model_serving_canary_platform.control import review_rollout_control
from model_serving_canary_platform.evaluation import RolloutEvaluator
from model_serving_canary_platform.inference import baseline_predict, canary_predict
from model_serving_canary_platform.models import (
    RolloutControlReport,
    RolloutEvaluationReport,
    RolloutHistoryReport,
)
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
        self.evaluator = RolloutEvaluator(
            baseline_model=settings.baseline_model_name,
            canary_model=settings.canary_model_name,
        )

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

    def evaluate_rollout(self, request: ApiRolloutEvaluationRequest) -> RolloutEvaluationReport:
        report = self.evaluator.evaluate(request)
        rollout_evaluations_total.labels(decision=report.decision).inc()
        rollout_priority_mismatch_rate.set(report.priority_mismatch_rate)
        rollout_average_score_delta.set(report.average_score_delta)
        return report

    def review_rollout_history(self, request: ApiRolloutHistoryRequest) -> RolloutHistoryReport:
        report = self.evaluator.review_history(request)
        rollout_history_reviews_total.labels(decision=report.decision).inc()
        rollout_stale_windows.set(report.stale_windows)
        rollout_rollback_evidence_complete.set(report.rollback_evidence_complete)
        return report

    def review_rollout_control(self, request: ApiRolloutControlRequest) -> RolloutControlReport:
        report = review_rollout_control(request)
        rollout_control_reviews_total.labels(decision=report.decision).inc()
        return report
