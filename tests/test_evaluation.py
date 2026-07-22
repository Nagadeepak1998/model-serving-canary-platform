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
    assert report.stale_windows == 1
    assert report.rollback_completion == "incomplete"


def test_rollout_history_accepts_completed_rollback_evidence() -> None:
    payload = json.loads((ROOT / "data" / "rollout_history.json").read_text())
    payload["windows"][-1]["rollback"] = {
        "completed_at": "2026-07-10T09:36:00Z",
        "owner": "sre-primary",
        "evidence_url": "https://example.invalid/changes/CHG-2048",
    }

    report = RolloutEvaluator("ticket-triage-v1", "ticket-triage-v2").review_history(
        RolloutHistoryRequest.model_validate(payload)
    )

    assert report.decision == "rollback"
    assert report.rollback_completion == "complete"
    assert report.rollback_evidence_complete is True


def test_stale_safe_stage_holds_promotion() -> None:
    safe = json.loads((ROOT / "data" / "rollout_eval_safe.json").read_text())
    request = RolloutHistoryRequest.model_validate(
        {
            "windows": [
                {
                    "observed_at": "2026-07-22T09:10:00Z",
                    "stage_started_at": "2026-07-22T09:00:00Z",
                    "evaluation": safe,
                },
                {
                    "observed_at": "2026-07-22T10:00:00Z",
                    "stage_started_at": "2026-07-22T09:15:00Z",
                    "evaluation": safe,
                },
            ]
        }
    )

    report = RolloutEvaluator("ticket-triage-v1", "ticket-triage-v2").review_history(request)

    assert report.decision == "hold"
    assert report.stale_windows == 1
