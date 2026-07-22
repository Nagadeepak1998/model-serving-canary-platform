from __future__ import annotations

from datetime import datetime

from model_serving_canary_platform.models import RolloutControlReport, RolloutControlRequest


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def review_rollout_control(request: RolloutControlRequest) -> RolloutControlReport:
    findings: list[str] = []
    reference_time = _timestamp(request.reference_time)
    approved_at = _timestamp(request.approval.approved_at)
    approval_age = int((reference_time - approved_at).total_seconds() // 60)

    if request.approval.requested_by == request.approval.approved_by:
        findings.append("rollout approval must be independent from the requester")
    if approval_age < 0:
        findings.append("rollout approval is dated after the reference time")
    elif approval_age > request.approval_max_age_minutes:
        findings.append(
            f"rollout approval is {approval_age} minutes old; maximum is "
            f"{request.approval_max_age_minutes}"
        )

    percentages = [stage.canary_percent for stage in request.stages]
    if percentages != sorted(percentages) or len(percentages) != len(set(percentages)):
        findings.append("canary stages must use unique, increasing traffic percentages")

    previous_completed_at = None
    for stage in request.stages:
        started_at = _timestamp(stage.started_at)
        completed_at = _timestamp(stage.completed_at) if stage.completed_at else None
        if completed_at is None:
            findings.append(f"{stage.canary_percent}% stage lacks completion evidence")
        elif completed_at < started_at:
            findings.append(f"{stage.canary_percent}% stage completed before it started")
        if previous_completed_at and started_at < previous_completed_at:
            findings.append(f"{stage.canary_percent}% stage started before the prior stage completed")
        if completed_at:
            previous_completed_at = completed_at

    rollback_required = request.rollback.required or any(
        stage.decision == "rollback" for stage in request.stages
    )
    rollback_complete = not rollback_required
    if rollback_required:
        rollback_complete = all(
            (
                request.rollback.completed_at,
                request.rollback.restored_model == request.baseline_model,
                request.rollback.evidence_uri,
            )
        )
        if not rollback_complete:
            findings.append("rollback lacks completion time, baseline restoration, or evidence URI")

    decision = "ready" if not findings else "blocked"
    return RolloutControlReport(
        decision=decision,
        release_id=request.release_id,
        reviewed_stages=len(request.stages),
        latest_canary_percent=percentages[-1],
        approval_age_minutes=approval_age,
        rollback_required=rollback_required,
        rollback_complete=rollback_complete,
        findings=findings,
    )
