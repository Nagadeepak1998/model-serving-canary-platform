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
