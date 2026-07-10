# Canary Rollout History Review

**Decision:** ROLLBACK

- Reviewed windows: 3
- Non-promote windows: 1
- Rollback windows: 1
- Latest decision: rollback

## Decision reasons

- 1 history window(s) require rollback

## Window evidence

| Observed at | Canary | Decision | Priority mismatch rate | Average score delta |
|---|---:|---|---:|---:|
| 2026-07-10T09:00:00Z | 10% | promote | 0.000 | 0.000 |
| 2026-07-10T09:15:00Z | 25% | promote | 0.000 | 0.000 |
| 2026-07-10T09:30:00Z | 50% | rollback | 1.000 | 0.145 |
