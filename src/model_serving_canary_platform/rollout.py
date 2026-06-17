from __future__ import annotations

import hashlib

from model_serving_canary_platform.models import ReleaseDecision


class CanaryRouter:
    def __init__(self, baseline_model: str, canary_model: str) -> None:
        self.baseline_model = baseline_model
        self.canary_model = canary_model

    def decide(self, ticket_id: str, canary_percent: int) -> ReleaseDecision:
        bucket = self._stable_bucket(ticket_id)
        selected = self.canary_model if bucket < canary_percent else self.baseline_model
        reason = f"Stable ticket hash bucket {bucket} compared with rollout threshold {canary_percent}."
        return ReleaseDecision(
            selected_model=selected,
            canary_percent=canary_percent,
            reason=reason,
        )

    @staticmethod
    def _stable_bucket(ticket_id: str) -> int:
        digest = hashlib.sha256(ticket_id.encode("utf-8")).hexdigest()
        return int(digest[:8], 16) % 100
