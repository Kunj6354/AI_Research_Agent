from fastapi.testclient import TestClient

from research_agent.main import app

client = TestClient(app)


def test_create_and_retrieve_research_job() -> None:
    create_response = client.post(
        "/api/v1/research",
        json={
            "topic": "Future of autonomous radar systems in India",
            "depth": "deep",
            "maximum_sources": 25,
            "time_range": {
                "from_date": "2024-01-01",
                "to_date": "2026-07-22",
            },
        },
    )

    assert create_response.status_code == 201

    created_job = create_response.json()

    assert created_job["research_id"].startswith("res_")
    assert created_job["topic"] == "Future of autonomous radar systems in India"
    assert created_job["depth"] == "deep"
    assert created_job["maximum_sources"] == 25
    assert created_job["status"] == "queued"
    assert created_job["created_at"] == created_job["updated_at"]

    retrieve_response = client.get(f"/api/v1/research/{created_job['research_id']}")

    assert retrieve_response.status_code == 200
    assert retrieve_response.json() == created_job


def test_create_research_job_rejects_invalid_request() -> None:
    response = client.post(
        "/api/v1/research",
        json={
            "topic": "AI",
            "maximum_sources": 100,
        },
    )

    assert response.status_code == 422

    error_locations = {tuple(error["loc"]) for error in response.json()["detail"]}

    assert ("body", "topic") in error_locations
    assert ("body", "maximum_sources") in error_locations


def test_create_research_job_rejects_reversed_date_range() -> None:
    response = client.post(
        "/api/v1/research",
        json={
            "topic": "AI research systems",
            "time_range": {
                "from_date": "2026-07-22",
                "to_date": "2024-01-01",
            },
        },
    )

    assert response.status_code == 422


def test_get_unknown_research_job_returns_not_found() -> None:
    response = client.get("/api/v1/research/res_missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Research job not found"}
