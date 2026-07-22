# Model Serving Canary Platform

`model-serving-canary-platform` is a production-shaped FastAPI service that demonstrates how to release a new model safely with deterministic canary routing, shadow evaluation, Prometheus metrics, and deployment-ready infrastructure assets.

## What it demonstrates

- Deterministic canary rollout decisions based on a stable hash of `ticket_id`
- Side-by-side baseline and canary prediction comparison for rollout review
- CLI and API rollout evaluation gates with promote, hold, and rollback decisions
- Multi-window rollout reviews with stage-staleness and rollback-completion evidence gates
- Staged traffic control reviews with fresh independent approval and ordered completion evidence
- Prometheus metrics for selected model traffic, latency, and shadow mismatches
- Docker, Kubernetes, and Terraform assets that make the repo recruiter-readable

## Architecture

```mermaid
flowchart LR
    Client["Support Tool"] --> API["FastAPI /predict"]
    API --> Router["Stable hash router"]
    Router -->|baseline| Base["Baseline model v1"]
    Router -->|canary| Canary["Canary model v2"]
    API --> Shadow["Shadow comparator"]
    API --> Gate["Rollout evaluation gate"]
    Gate --> History["History and staleness review"]
    History --> Rollback["Rollback evidence gate"]
    Rollback --> Control["Approval and traffic-stage control"]
    Base --> Shadow
    Canary --> Shadow
    Shadow --> Metrics["Prometheus metrics"]
    History --> Metrics
```

## Project layout

```text
app/                         FastAPI entrypoint, config, metrics, service layer
src/model_serving_canary_platform/  rollout and inference domain logic
tests/                       API and routing tests
data/                        Evaluation fixtures and rollout history manifest
infra/docker/                Container image
infra/k8s/                   Kubernetes manifests
infra/terraform/             Terraform deployment skeleton
docs/CASE_STUDY.md           Portfolio narrative
```

## Quickstart

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .[dev]
pytest
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Prediction example:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "INC-10091",
    "account_tier": "enterprise",
    "minutes_open": 215,
    "message_length": 890,
    "sentiment_score": -0.51,
    "similar_incidents": 5,
    "escalation_keywords": 3,
    "canary_percent": 50
  }'
```

Metrics endpoint:

```bash
curl http://127.0.0.1:8000/metrics
```

Rollout evaluation API:

```bash
curl -X POST http://127.0.0.1:8000/rollout/evaluate \
  -H "Content-Type: application/json" \
  --data @data/rollout_eval_safe.json
```

CLI rollout gate:

```bash
make eval-safe
make eval-risky
make history-report
make control-review
make control-review-blocked
```

`make history-report` replays three dated rollout windows and writes
`reports/rollout-history.json` plus the tracked reviewer summary
`reports/rollout-history.md`. The sample ends in `rollback`, so the Make target
accepts exit code `2` as the expected deployment-gate result. The final 50%
stage is also 45 minutes old against a 30-minute limit and has no rollback
completion record, making the operational gap explicit in both reports.

Each history window can set `stage_started_at` and `max_stage_age_minutes`.
Rollback windows close only when `rollback` includes a completion timestamp,
owner, and evidence URL; this is evidence metadata, not a claim that a live
rollback occurred.

Rollout history API:

```bash
curl -X POST http://127.0.0.1:8000/rollout/history \
  -H "Content-Type: application/json" \
  --data @data/rollout_history.json
```

`make control-review` proves a 10% to 25% to 50% rollout has ordered completion
evidence and fresh independent approval. The blocked fixture exits `2` when
approval separation and rollback-completion evidence are missing.

```bash
curl -X POST http://127.0.0.1:8000/rollout/control-review \
  -H "Content-Type: application/json" \
  --data @data/rollout_control_ready.json
```

## Docker

```bash
docker compose up --build
```

## Testing

```bash
pytest
python scripts/smoke_predict.py
make eval-safe
make eval-risky
make history-report
make control-review
make control-review-blocked
```

## Kubernetes and Terraform

- Kubernetes manifests are in `infra/k8s/`.
- Terraform mirrors the deployment shape in `infra/terraform/`.
- Both assume an external cluster and published container image.

## Observability and security notes

- `/metrics` exposes Prometheus-compatible counters and latency histograms.
- Rollout evaluation records the latest mismatch rate, average score delta, and decision count.
- History reviews expose stale-stage counts and rollback-evidence completeness without storing ticket payloads in metrics.
- Control-review metrics omit requester and approver identities from labels.
- Stable hash routing avoids per-request randomness during rollout validation.
- The repo uses environment-based configuration and does not include secrets.

## Limitations

- The models are deterministic heuristics, not trained artifacts.
- Progressive delivery is implemented in-app rather than through a service mesh.
- History fixtures are deterministic release evidence, not live production telemetry.
- Evidence URLs in fixtures are illustrative and are never fetched or treated as proof of a production change.
- Control-review evidence URIs are presence-checked; external artifacts are not fetched or attested.
- Terraform is a deployment skeleton and was not applied to a live cluster in this run.
