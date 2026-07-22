from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_returns_shadow_comparison() -> None:
    payload = {
        "ticket_id": "INC-40001",
        "account_tier": "enterprise",
        "minutes_open": 150,
        "message_length": 850,
        "sentiment_score": -0.42,
        "similar_incidents": 5,
        "escalation_keywords": 2,
        "canary_percent": 100,
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["selected_model"] == "ticket-triage-v2"
    assert body["canary_percent"] == 100
    assert "route_reason" in body
    assert body["canary_risk_score"] >= body["baseline_risk_score"]


def test_evaluate_rollout_returns_release_decision() -> None:
    payload = {
        "canary_percent": 25,
        "max_priority_mismatch_rate": 0.25,
        "max_average_score_delta": 0.14,
        "cases": [
            {
                "ticket_id": "INC-10092",
                "account_tier": "business",
                "minutes_open": 43,
                "message_length": 230,
                "sentiment_score": 0.14,
                "similar_incidents": 1,
                "escalation_keywords": 0,
                "expected_priority": "low",
            }
        ],
    }

    response = client.post("/rollout/evaluate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] in {"promote", "hold", "rollback"}
    assert body["case_count"] == 1
    assert body["cases"][0]["ticket_id"] == "INC-10092"


def test_rollout_evaluate_alias_returns_release_decision() -> None:
    payload = {
        "canary_percent": 25,
        "cases": [
            {
                "ticket_id": "INC-10092",
                "account_tier": "business",
                "minutes_open": 43,
                "message_length": 230,
                "sentiment_score": 0.14,
                "similar_incidents": 1,
                "escalation_keywords": 0,
                "expected_priority": "medium",
            }
        ],
    }

    response = client.post("/rollout/evaluate", json=payload)

    assert response.status_code == 200
    assert response.json()["case_count"] == 1


def test_rollout_history_returns_multi_window_decision() -> None:
    payload = {
        "windows": [
            {"observed_at": "2026-07-10T09:00:00Z", "evaluation": {
                "canary_percent": 10,
                "cases": [{
                    "ticket_id": "INC-10092", "account_tier": "business",
                    "minutes_open": 43, "message_length": 230,
                    "sentiment_score": 0.14, "similar_incidents": 1,
                    "escalation_keywords": 0, "expected_priority": "medium"
                }]
            }},
            {"observed_at": "2026-07-10T09:15:00Z", "evaluation": {
                "canary_percent": 25,
                "cases": [{
                    "ticket_id": "INC-10092", "account_tier": "business",
                    "minutes_open": 43, "message_length": 230,
                    "sentiment_score": 0.14, "similar_incidents": 1,
                    "escalation_keywords": 0, "expected_priority": "medium"
                }]
            }}
        ]
    }

    response = client.post("/rollout/history", json=payload)

    assert response.status_code == 200
    assert response.json()["decision"] == "promote"
    assert response.json()["reviewed_windows"] == 2
    assert response.json()["stale_windows"] == 0


def test_rollout_control_review_returns_auditable_decision() -> None:
    payload = {
        "release_id": "ticket-triage-v2-api", "baseline_model": "ticket-triage-v1",
        "canary_model": "ticket-triage-v2", "reference_time": "2026-07-22T16:00:00Z",
        "approval": {"requested_by": "ml-platform-engineer", "approved_by": "sre-release-manager", "approved_at": "2026-07-22T15:30:00Z"},
        "stages": [{"canary_percent": 10, "started_at": "2026-07-22T15:32:00Z", "completed_at": "2026-07-22T15:40:00Z", "decision": "promote", "evidence_uri": "reports/rollout-10.json"}],
    }
    response = client.post("/rollout/control-review", json=payload)
    assert response.status_code == 200
    assert response.json()["decision"] == "ready"
    assert response.json()["approval_age_minutes"] == 30
