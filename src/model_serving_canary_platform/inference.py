from __future__ import annotations

from model_serving_canary_platform.models import PredictionFeatures, PredictionResult


def _priority_from_score(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.55:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"


def baseline_predict(features: PredictionFeatures, model_name: str) -> PredictionResult:
    score = (
        0.28
        + min(features.minutes_open / 600, 0.22)
        + min(features.message_length / 4000, 0.16)
        + (0.18 if features.account_tier.lower() == "enterprise" else 0.05)
        + min(features.similar_incidents * 0.04, 0.12)
        + min(features.escalation_keywords * 0.05, 0.14)
        - (features.sentiment_score * 0.08)
    )
    bounded = max(0.0, min(round(score, 3), 1.0))
    priority = _priority_from_score(bounded)
    return PredictionResult(
        model=model_name,
        risk_score=bounded,
        priority=priority,
        summary=f"Baseline model routed ticket as {priority}.",
    )


def canary_predict(features: PredictionFeatures, model_name: str) -> PredictionResult:
    baseline = baseline_predict(features, model_name)
    adjusted = baseline.risk_score
    if features.escalation_keywords >= 2:
        adjusted += 0.08
    if features.similar_incidents >= 4:
        adjusted += 0.05
    if features.sentiment_score < -0.35:
        adjusted += 0.04
    bounded = max(0.0, min(round(adjusted, 3), 1.0))
    priority = _priority_from_score(bounded)
    return PredictionResult(
        model=model_name,
        risk_score=bounded,
        priority=priority,
        summary=f"Canary model routed ticket as {priority}.",
    )
