from __future__ import annotations

from model_serving_canary_platform.inference import baseline_predict, canary_predict
from model_serving_canary_platform.models import (
    RolloutEvaluationCaseResult,
    RolloutEvaluationReport,
    RolloutEvaluationRequest,
    RolloutHistoryReport,
    RolloutHistoryRequest,
    RolloutHistoryWindowResult,
)
from model_serving_canary_platform.shadow import ShadowComparator


class RolloutEvaluator:
    def __init__(self, baseline_model: str, canary_model: str) -> None:
        self.baseline_model = baseline_model
        self.canary_model = canary_model
        self.shadow = ShadowComparator()

    def evaluate(self, request: RolloutEvaluationRequest) -> RolloutEvaluationReport:
        case_results: list[RolloutEvaluationCaseResult] = []

        for case in request.cases:
            baseline = baseline_predict(case, self.baseline_model)
            canary = canary_predict(case, self.canary_model)
            comparison = self.shadow.compare(baseline, canary)
            expected_match = None
            if case.expected_priority is not None:
                expected_match = canary.priority == case.expected_priority

            case_results.append(
                RolloutEvaluationCaseResult(
                    ticket_id=case.ticket_id,
                    baseline_priority=comparison.baseline_priority,
                    canary_priority=comparison.canary_priority,
                    score_delta=comparison.absolute_score_delta,
                    priority_changed=comparison.priority_changed,
                    expected_priority=case.expected_priority,
                    expected_priority_matched=expected_match,
                )
            )

        case_count = len(case_results)
        mismatch_count = sum(1 for case in case_results if case.priority_changed)
        priority_mismatch_rate = round(mismatch_count / case_count, 3)
        average_score_delta = round(sum(case.score_delta for case in case_results) / case_count, 3)
        max_score_delta = max(case.score_delta for case in case_results)

        expected_cases = [case for case in case_results if case.expected_priority_matched is not None]
        expected_priority_miss_rate = None
        if expected_cases:
            expected_misses = sum(1 for case in expected_cases if not case.expected_priority_matched)
            expected_priority_miss_rate = round(expected_misses / len(expected_cases), 3)

        reasons: list[str] = []
        if priority_mismatch_rate > request.max_priority_mismatch_rate:
            reasons.append(
                "priority mismatch rate "
                f"{priority_mismatch_rate} exceeds threshold {request.max_priority_mismatch_rate}"
            )
        if average_score_delta > request.max_average_score_delta:
            reasons.append(
                "average score delta "
                f"{average_score_delta} exceeds threshold {request.max_average_score_delta}"
            )
        if expected_priority_miss_rate is not None and expected_priority_miss_rate > 0:
            reasons.append(f"expected priority miss rate is {expected_priority_miss_rate}")

        decision = "promote" if not reasons else "hold"
        if priority_mismatch_rate >= 0.5 or max_score_delta >= 0.25:
            decision = "rollback"

        if not reasons:
            reasons.append("canary stayed within rollout guardrails")

        return RolloutEvaluationReport(
            decision=decision,
            canary_percent=request.canary_percent,
            case_count=case_count,
            priority_mismatch_rate=priority_mismatch_rate,
            average_score_delta=average_score_delta,
            max_score_delta=max_score_delta,
            expected_priority_miss_rate=expected_priority_miss_rate,
            reasons=reasons,
            cases=case_results,
        )

    def review_history(self, request: RolloutHistoryRequest) -> RolloutHistoryReport:
        windows: list[RolloutHistoryWindowResult] = []
        for window in request.windows:
            report = self.evaluate(window.evaluation)
            windows.append(
                RolloutHistoryWindowResult(
                    observed_at=window.observed_at,
                    decision=report.decision,
                    canary_percent=report.canary_percent,
                    priority_mismatch_rate=report.priority_mismatch_rate,
                    average_score_delta=report.average_score_delta,
                )
            )

        non_promote_windows = sum(window.decision != "promote" for window in windows)
        rollback_windows = sum(window.decision == "rollback" for window in windows)
        latest_decision = windows[-1].decision
        reasons: list[str] = []
        decision = "promote"
        if rollback_windows:
            decision = "rollback"
            reasons.append(f"{rollback_windows} history window(s) require rollback")
        elif non_promote_windows > request.max_non_promote_windows or latest_decision != "promote":
            decision = "hold"
            reasons.append(
                f"{non_promote_windows} non-promote window(s); latest decision is {latest_decision}"
            )
        else:
            reasons.append("rollout history stayed within promotion guardrails")

        return RolloutHistoryReport(
            decision=decision,
            reviewed_windows=len(windows),
            non_promote_windows=non_promote_windows,
            rollback_windows=rollback_windows,
            latest_decision=latest_decision,
            reasons=reasons,
            windows=windows,
        )
