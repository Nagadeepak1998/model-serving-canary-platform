from __future__ import annotations

from datetime import datetime

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
            stage_age_minutes = None
            if window.stage_started_at:
                observed_at = datetime.fromisoformat(window.observed_at.replace("Z", "+00:00"))
                started_at = datetime.fromisoformat(window.stage_started_at.replace("Z", "+00:00"))
                stage_age_minutes = int((observed_at - started_at).total_seconds() // 60)
            stale = (
                stage_age_minutes is not None
                and stage_age_minutes > window.max_stage_age_minutes
            )
            windows.append(
                RolloutHistoryWindowResult(
                    observed_at=window.observed_at,
                    decision=report.decision,
                    canary_percent=report.canary_percent,
                    priority_mismatch_rate=report.priority_mismatch_rate,
                    average_score_delta=report.average_score_delta,
                    stage_age_minutes=stage_age_minutes,
                    stale=stale,
                )
            )

        non_promote_windows = sum(window.decision != "promote" for window in windows)
        rollback_windows = sum(window.decision == "rollback" for window in windows)
        stale_windows = sum(window.stale for window in windows)
        latest_decision = windows[-1].decision
        rollback_evidence_complete = all(
            source.rollback is not None
            for source, result in zip(request.windows, windows, strict=True)
            if result.decision == "rollback"
        )
        rollback_completion = (
            "not-required"
            if rollback_windows == 0
            else "complete" if rollback_evidence_complete else "incomplete"
        )
        reasons: list[str] = []
        decision = "promote"
        if rollback_windows:
            decision = "rollback"
            reasons.append(f"{rollback_windows} history window(s) require rollback")
            if not rollback_evidence_complete:
                reasons.append("rollback completion evidence is missing")
        elif stale_windows:
            decision = "hold"
            reasons.append(f"{stale_windows} rollout stage(s) exceeded their age limit")
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
            stale_windows=stale_windows,
            latest_decision=latest_decision,
            rollback_completion=rollback_completion,
            rollback_evidence_complete=rollback_evidence_complete,
            reasons=reasons,
            windows=windows,
        )
