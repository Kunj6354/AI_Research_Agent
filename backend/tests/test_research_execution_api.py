from dataclasses import dataclass

from fastapi.testclient import TestClient

from research_agent.api.research import resolve_provider_bundle
from research_agent.integrations.provider_factory import ProviderBundle
from research_agent.main import app
from research_agent.models.research import (
    ResearchCitation,
    ResearchCreateRequest,
    ResearchPlan,
    ResearchReport,
    ResearchSource,
)
from research_agent.services.research_service import (
    get_research_service,
)
from research_agent.workflows.research_workflow import ResearchWorkflow


class FakePlanner:
    def plan(
        self,
        request: ResearchCreateRequest,
    ) -> ResearchPlan:
        return ResearchPlan(
            queries=[
                f"{request.topic} architecture",
                f"{request.topic} evidence",
            ]
        )


class FakeSearcher:
    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        request: ResearchCreateRequest,
    ) -> list[ResearchSource]:
        del request

        sources = [
            ResearchSource(
                source_id="src_primary",
                title="Primary evidence",
                url="https://example.com/primary",
                content=f"Evidence for query: {query}",
                relevance_score=0.95,
            ),
            ResearchSource(
                source_id="src_secondary",
                title="Secondary evidence",
                url="https://example.com/secondary",
                content="Supporting evidence.",
                relevance_score=0.80,
            ),
        ]

        return sources[:maximum_results]


class FakeWriter:
    def write(
        self,
        request: ResearchCreateRequest,
        sources: list[ResearchSource],
    ) -> ResearchReport:
        primary = sources[0]

        return ResearchReport(
            topic=request.topic,
            summary="Synthetic evidence supports the report.",
            findings=[
                "The research workflow executed successfully.",
                "The final report retained verified evidence.",
            ],
            citations=[
                ResearchCitation(
                    source_id=primary.source_id,
                    title=primary.title,
                    url=primary.url,
                )
            ],
            sources=sources,
        )


class FailingPlanner:
    def plan(
        self,
        request: ResearchCreateRequest,
    ) -> ResearchPlan:
        del request
        raise RuntimeError("synthetic planner failure")


@dataclass
class NeverCalledSearcher:
    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        request: ResearchCreateRequest,
    ) -> list[ResearchSource]:
        raise AssertionError("searcher must not execute after planner failure")


@dataclass
class NeverCalledWriter:
    def write(
        self,
        request: ResearchCreateRequest,
        sources: list[ResearchSource],
    ) -> ResearchReport:
        raise AssertionError("writer must not execute after planner failure")


def successful_bundle() -> ProviderBundle:
    return ProviderBundle(
        workflow=ResearchWorkflow(
            planner=FakePlanner(),
            searcher=FakeSearcher(),
            writer=FakeWriter(),
        )
    )


def failing_bundle() -> ProviderBundle:
    return ProviderBundle(
        workflow=ResearchWorkflow(
            planner=FailingPlanner(),
            searcher=NeverCalledSearcher(),
            writer=NeverCalledWriter(),
        )
    )


def reset_service() -> None:
    get_research_service.cache_clear()


def test_research_job_runs_to_completed_report() -> None:
    reset_service()

    app.dependency_overrides[resolve_provider_bundle] = successful_bundle

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/api/v1/research",
                json={
                    "topic": "Evidence driven AI research",
                    "depth": "quick",
                    "maximum_sources": 5,
                },
            )

            assert create_response.status_code == 201

            created = create_response.json()

            assert created["status"] == "queued"
            assert created["report"] is None
            assert created["error"] is None

            research_id = created["research_id"]

            run_response = client.post(f"/api/v1/research/{research_id}/run")

            assert run_response.status_code == 200

            completed = run_response.json()

            assert completed["status"] == "completed"
            assert completed["error"] is None
            assert completed["report"] is not None

            report = completed["report"]

            assert report["topic"] == ("Evidence driven AI research")
            assert report["summary"]
            assert len(report["findings"]) == 2
            assert len(report["citations"]) == 1
            assert report["citations"][0]["source_id"] == ("src_primary")

            get_response = client.get(f"/api/v1/research/{research_id}")

            assert get_response.status_code == 200
            assert get_response.json() == completed
    finally:
        app.dependency_overrides.clear()
        reset_service()


def test_research_job_failure_is_persisted_as_failed_state() -> None:
    reset_service()

    app.dependency_overrides[resolve_provider_bundle] = failing_bundle

    try:
        with TestClient(app) as client:
            create_response = client.post(
                "/api/v1/research",
                json={
                    "topic": "Failure handling research",
                    "maximum_sources": 5,
                },
            )

            research_id = create_response.json()["research_id"]

            run_response = client.post(f"/api/v1/research/{research_id}/run")

            assert run_response.status_code == 200

            failed = run_response.json()

            assert failed["status"] == "failed"
            assert failed["report"] is None
            assert "synthetic planner failure" in failed["error"]

            get_response = client.get(f"/api/v1/research/{research_id}")

            assert get_response.status_code == 200
            assert get_response.json()["status"] == "failed"
    finally:
        app.dependency_overrides.clear()
        reset_service()


def test_run_unknown_research_job_returns_not_found() -> None:
    reset_service()

    app.dependency_overrides[resolve_provider_bundle] = successful_bundle

    try:
        with TestClient(app) as client:
            response = client.post("/api/v1/research/res_missing/run")

            assert response.status_code == 404
            assert response.json() == {"detail": "Research job not found"}
    finally:
        app.dependency_overrides.clear()
        reset_service()


def test_completed_research_job_cannot_run_again() -> None:
    reset_service()

    app.dependency_overrides[resolve_provider_bundle] = successful_bundle

    try:
        with TestClient(app) as client:
            created = client.post(
                "/api/v1/research",
                json={
                    "topic": "Single execution contract",
                    "maximum_sources": 5,
                },
            ).json()

            research_id = created["research_id"]

            first_run = client.post(f"/api/v1/research/{research_id}/run")

            assert first_run.status_code == 200
            assert first_run.json()["status"] == "completed"

            second_run = client.post(f"/api/v1/research/{research_id}/run")

            assert second_run.status_code == 409
            assert "cannot run from status: completed" in (second_run.json()["detail"])
    finally:
        app.dependency_overrides.clear()
        reset_service()
