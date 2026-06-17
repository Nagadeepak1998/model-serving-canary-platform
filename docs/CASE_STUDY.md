# Case Study: Model Serving Canary Platform

## Problem

A team wants to release a new support-ticket risk model without switching all traffic at once or losing visibility into how predictions differ from the stable model.

## Solution

This project exposes a FastAPI service that deterministically routes requests between baseline and canary models using a stable hash of `ticket_id`. It also runs the non-selected model in shadow mode so the service can record score deltas and priority mismatches for rollout review.

## Production-shaped elements

- Deterministic rollout control with a caller override for release testing.
- Prometheus metrics for selected-model traffic, shadow mismatches, and request latency.
- Docker, Docker Compose, Kubernetes manifests, and Terraform deployment skeleton.
- Tests covering rollout stability, API behavior, and shadow comparison.

## What this demonstrates

- Safe model release mechanics for MLOps and AI platform roles.
- Service-oriented implementation rather than notebook-style experimentation.
- Recruiter-readable operational thinking: health checks, metrics, deployment shape, and rollout documentation.
