from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_serving_canary_platform.control import review_rollout_control
from model_serving_canary_platform.evaluation import RolloutEvaluator
from model_serving_canary_platform.models import (
    RolloutControlRequest,
    RolloutEvaluationRequest,
    RolloutHistoryRequest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate canary rollout guardrails.")
    parser.add_argument("mode", choices=("evaluate", "history", "control-review"))
    parser.add_argument("input", type=Path, help="Path to rollout JSON input.")
    parser.add_argument("--output", type=Path, help="Optional path for the JSON report.")
    parser.add_argument("--markdown", type=Path, help="Optional history Markdown report path.")
    return parser


def render_control_markdown(report) -> str:
    findings = "\n".join(f"- {finding}" for finding in report.findings) or "- None"
    return f"""# Canary Rollout Control Review

**Decision:** {report.decision.upper()}

- Release: `{report.release_id}`
- Reviewed stages: {report.reviewed_stages}
- Latest canary traffic: {report.latest_canary_percent}%
- Approval age: {report.approval_age_minutes} minutes
- Rollback required: {str(report.rollback_required).lower()}
- Rollback complete: {str(report.rollback_complete).lower()}

## Findings

{findings}
"""


def render_history_markdown(report) -> str:
    rows = "\n".join(
        f"| {window.observed_at} | {window.canary_percent}% | {window.decision} | "
        f"{window.priority_mismatch_rate:.3f} | {window.average_score_delta:.3f} | "
        f"{window.stage_age_minutes if window.stage_age_minutes is not None else '-'} | "
        f"{'yes' if window.stale else 'no'} |"
        for window in report.windows
    )
    reasons = "\n".join(f"- {reason}" for reason in report.reasons)
    return f"""# Canary Rollout History Review

**Decision:** {report.decision.upper()}

- Reviewed windows: {report.reviewed_windows}
- Non-promote windows: {report.non_promote_windows}
- Rollback windows: {report.rollback_windows}
- Stale windows: {report.stale_windows}
- Latest decision: {report.latest_decision}
- Rollback completion: {report.rollback_completion}

## Decision reasons

{reasons}

## Window evidence

| Observed at | Canary | Decision | Priority mismatch rate | Average score delta | Stage age (min) | Stale |
|---|---:|---|---:|---:|---:|---|
{rows}
"""


def main() -> int:
    args = build_parser().parse_args()
    payload = json.loads(args.input.read_text())
    evaluator = RolloutEvaluator(
        baseline_model="ticket-triage-v1",
        canary_model="ticket-triage-v2",
    )
    if args.mode == "control-review":
        report = review_rollout_control(RolloutControlRequest.model_validate(payload))
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(render_control_markdown(report))
    elif args.mode == "history":
        report = evaluator.review_history(RolloutHistoryRequest.model_validate(payload))
        if args.markdown:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(render_history_markdown(report))
    else:
        report = evaluator.evaluate(RolloutEvaluationRequest.model_validate(payload))
    output = json.dumps(report.model_dump(), indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n")
    else:
        print(output)

    return 0 if report.decision in {"promote", "ready"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
