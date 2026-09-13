from fastapi.testclient import TestClient

from research_agent.core.config import get_settings
from research_agent.integrations.clients import (
    get_openai_client,
    get_tavily_client,
)
from research_agent.main import app
from research_agent.services.research_service import get_research_service


def clear_caches() -> None:
    get_settings.cache_clear()
    get_openai_client.cache_clear()
    get_tavily_client.cache_clear()
    get_research_service.cache_clear()


def test_provider_readiness_reports_unconfigured_state(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    clear_caches()

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/research/providers/readiness")

        assert response.status_code == 200
        assert response.json() == {
            "openai_configured": False,
            "openai_model_configured": False,
            "tavily_configured": False,
            "ready": False,
        }
    finally:
        clear_caches()


def test_run_returns_503_when_provider_keys_are_missing(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    clear_caches()

    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/v1/research",
                json={
                    "topic": "Provider readiness boundary",
                    "maximum_sources": 5,
                },
            )

            assert created.status_code == 201

            research_id = created.json()["research_id"]

            response = client.post(f"/api/v1/research/{research_id}/run")

            assert response.status_code == 503
            assert "Research providers are not ready" in (response.json()["detail"])

            job = client.get(f"/api/v1/research/{research_id}")

            assert job.status_code == 200
            assert job.json()["status"] == "queued"
            assert job.json()["report"] is None
            assert job.json()["error"] is None
    finally:
        clear_caches()
