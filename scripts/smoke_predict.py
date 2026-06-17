from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app


client = TestClient(app)

payload = {
    "ticket_id": "INC-10091",
    "account_tier": "enterprise",
    "minutes_open": 215,
    "message_length": 890,
    "sentiment_score": -0.51,
    "similar_incidents": 5,
    "escalation_keywords": 3,
    "canary_percent": 50,
}

response = client.post("/predict", json=payload)
response.raise_for_status()
print(response.json())
