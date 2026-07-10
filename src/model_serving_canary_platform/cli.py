from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_serving_canary_platform.evaluation import RolloutEvaluator
from model_serving_canary_platform.models import RolloutEvaluationRequest, RolloutHistoryRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate canary rollout guardrails.")
    parser.add_argument("mode", choices=("evaluate", "history"))
    parser.add_argument("input", type=Path, help="Path to rollout JSON input.")
    parser.add_argument("--output", type=Path, help="Optional path for the JSON report.")
    parser.add_argument("--markdown", type=Path, help="Optional history Markdown report path.")
    return parser


def render_history_markdown(report) -> str:
    rows = "\n".join(
        f"| {window.observed_at} | {window.canary_percent}% | {window.decision} | "
        f"{window.priority_mismatch_rate:.3f} | {window.average_score_delta:.3f} |"
        for window in report.windows
    )
    reasons = "\n".join(f"- {reason}" for reason in report.reasons)
    return f"""# Canary Rollout History Review

**Decision:** {report.decision.upper()}

- Reviewed windows: {report.reviewed_windows}
- Non-promote windows: {report.non_promote_windows}
- Rollback windows: {report.rollback_windows}
- Latest decision: {report.latest_decision}

## Decision reasons

{reasons}

## Window evidence

| Observed at | Canary | Decision | Priority mismatch rate | Average score delta |
|---|---:|---|---:|---:|
{rows}
"""


def main() -> int:
    args = build_parser().parse_args()
    payload = json.loads(args.input.read_text())
    evaluator = RolloutEvaluator(
        baseline_model="ticket-triage-v1",
        canary_model="ticket-triage-v2",
    )
    if args.mode == "history":
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

    return 0 if report.decision == "promote" else 2


if __name__ == "__main__":
    raise SystemExit(main())
