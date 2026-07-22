from datetime import datetime

from fastapi.testclient import TestClient

from research_agent.main import app

client = TestClient(app)


def test_health_check_returns_service_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "healthy"
    assert payload["service"] == "StackOre AI Research Agent"
    assert payload["version"] == "0.1.0"
    assert payload["environment"] == "development"

    timestamp = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
    assert timestamp.tzinfo is not None


def test_openapi_contains_health_endpoint() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/health" in response.json()["paths"]
