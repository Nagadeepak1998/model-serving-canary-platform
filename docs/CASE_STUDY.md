# Case Study: Model Serving Canary Platform

## Problem

A team wants to release a new support-ticket risk model without switching all traffic at once or losing visibility into how predictions differ from the stable model.

## Solution

This project exposes a FastAPI service that deterministically routes requests between baseline and canary models using a stable hash of `ticket_id`. It also runs the non-selected model in shadow mode so the service can record score deltas and priority mismatches for rollout review.

The upgraded workflow adds rollout evaluation and history gates. Release engineers can submit representative tickets through the API or CLI, then replay dated rollout windows to catch a canary that was safe at 10% and 25% traffic but regressed at 50%. The history review produces a promote, hold, or rollback decision plus a Markdown release record.

## Production-shaped elements

- Deterministic rollout control with a caller override for release testing.
- Promotion-readiness evaluator exposed through `/rollout/evaluate` and the `canary-rollout-eval` CLI.
- Multi-window readiness review exposed through `/rollout/history`, the CLI, and `make history-report`.
- Prometheus metrics for selected-model traffic, shadow mismatches, and request latency.
- Docker, Docker Compose, Kubernetes manifests, and Terraform deployment skeleton.
- Tests covering rollout stability, API behavior, shadow comparison, safe/risky rollout gates, and history escalation.

## What this demonstrates

- Safe model release mechanics for MLOps and AI platform roles.
- How to convert model-shadow data into an operational release decision.
- How to preserve reviewer-readable evidence across progressive traffic stages.
- Service-oriented implementation rather than notebook-style experimentation.
- Recruiter-readable operational thinking: health checks, metrics, deployment shape, and rollout documentation.
