import json
from pathlib import Path

from model_serving_canary_platform.control import review_rollout_control
from model_serving_canary_platform.models import RolloutControlRequest

ROOT = Path(__file__).resolve().parents[1]


def _review(name: str):
    payload = json.loads((ROOT / "data" / name).read_text())
    return review_rollout_control(RolloutControlRequest.model_validate(payload))


def test_complete_staged_rollout_is_ready() -> None:
    report = _review("rollout_control_ready.json")
    assert report.decision == "ready"
    assert report.reviewed_stages == 3
    assert report.approval_age_minutes == 30
    assert report.findings == []


def test_missing_rollback_handoff_blocks_release() -> None:
    report = _review("rollout_control_blocked.json")
    assert report.decision == "blocked"
    assert report.rollback_required is True
    assert report.rollback_complete is False
    assert "rollout approval must be independent from the requester" in report.findings
    assert "rollback lacks completion time, baseline restoration, or evidence URI" in report.findings
