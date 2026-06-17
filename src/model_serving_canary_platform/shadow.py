from __future__ import annotations

from model_serving_canary_platform.models import PredictionResult, ShadowComparison


class ShadowComparator:
    def compare(
        self,
        baseline: PredictionResult,
        canary: PredictionResult,
    ) -> ShadowComparison:
        return ShadowComparison(
            absolute_score_delta=round(abs(baseline.risk_score - canary.risk_score), 3),
            priority_changed=baseline.priority != canary.priority,
            baseline_priority=baseline.priority,
            canary_priority=canary.priority,
        )
