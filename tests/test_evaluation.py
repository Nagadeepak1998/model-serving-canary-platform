import json
from pathlib import Path

from model_serving_canary_platform.evaluation import RolloutEvaluator
from model_serving_canary_platform.models import RolloutEvaluationRequest, RolloutHistoryRequest


ROOT = Path(__file__).resolve().parents[1]


def _load_request(name: str) -> RolloutEvaluationRequest:
    payload = json.loads((ROOT / "data" / name).read_text())
    return RolloutEvaluationRequest.model_validate(payload)


def test_safe_rollout_promotes() -> None:
    report = RolloutEvaluator("ticket-triage-v1", "ticket-triage-v2").evaluate(
        _load_request("rollout_eval_safe.json")
    )

    assert report.decision == "promote"
    assert report.case_count == 3
    assert report.priority_mismatch_rate <= 0.25


def test_risky_rollout_blocks_promotion() -> None:
    report = RolloutEvaluator("ticket-triage-v1", "ticket-triage-v2").evaluate(
        _load_request("rollout_eval_risky.json")
    )

    assert report.decision in {"hold", "rollback"}
    assert report.reasons


def test_rollout_history_escalates_a_late_regression() -> None:
    payload = json.loads((ROOT / "data" / "rollout_history.json").read_text())

    report = RolloutEvaluator("ticket-triage-v1", "ticket-triage-v2").review_history(
        RolloutHistoryRequest.model_validate(payload)
    )

    assert report.decision == "rollback"
    assert report.reviewed_windows == 3
    assert report.rollback_windows == 1
    assert report.latest_decision == "rollback"
