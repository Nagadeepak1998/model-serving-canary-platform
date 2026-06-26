from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_serving_canary_platform.evaluation import RolloutEvaluator
from model_serving_canary_platform.models import RolloutEvaluationRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate canary rollout guardrails.")
    parser.add_argument("input", type=Path, help="Path to rollout evaluation JSON.")
    parser.add_argument("--output", type=Path, help="Optional path for the JSON report.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = json.loads(args.input.read_text())
    request = RolloutEvaluationRequest.model_validate(payload)
    report = RolloutEvaluator(
        baseline_model="ticket-triage-v1",
        canary_model="ticket-triage-v2",
    ).evaluate(request)
    output = json.dumps(report.model_dump(), indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n")
    else:
        print(output)

    return 0 if report.decision == "promote" else 2


if __name__ == "__main__":
    raise SystemExit(main())
