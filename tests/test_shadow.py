from model_serving_canary_platform.inference import baseline_predict, canary_predict
from model_serving_canary_platform.models import PredictionFeatures
from model_serving_canary_platform.shadow import ShadowComparator


def test_shadow_detects_priority_change() -> None:
    features = PredictionFeatures(
        ticket_id="INC-77777",
        account_tier="enterprise",
        minutes_open=320,
        message_length=1200,
        sentiment_score=-0.8,
        similar_incidents=8,
        escalation_keywords=4,
    )

    baseline = baseline_predict(features, "baseline")
    canary = canary_predict(features, "canary")
    result = ShadowComparator().compare(baseline, canary)

    assert result.absolute_score_delta >= 0
    assert result.canary_priority in {"high", "critical"}
