import pytest

from research_agent.models.research import (
    ResearchCitation,
    ResearchCreateRequest,
    ResearchPlan,
    ResearchReport,
    ResearchSource,
    ResearchStatus,
)
from research_agent.workflows.research_workflow import (
    ResearchWorkflow,
    ResearchWorkflowError,
)


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

        if "architecture" in query:
            return [
                ResearchSource(
                    source_id="src_architecture",
                    title="Architecture source",
                    url="https://example.com/architecture",
                    content="Architecture evidence.",
                    relevance_score=0.95,
                ),
                ResearchSource(
                    source_id="src_duplicate_lower",
                    title="Duplicate lower-ranked source",
                    url="https://example.com/shared",
                    content="Lower-ranked duplicate.",
                    relevance_score=0.40,
                ),
            ][:maximum_results]

        return [
            ResearchSource(
                source_id="src_evidence",
                title="Evidence source",
                url="https://example.com/evidence",
                content="Evidence-backed findings.",
                relevance_score=0.90,
            ),
            ResearchSource(
                source_id="src_duplicate_higher",
                title="Duplicate higher-ranked source",
                url="https://example.com/shared",
                content="Higher-ranked duplicate.",
                relevance_score=0.80,
            ),
        ][:maximum_results]


class FakeWriter:
    def write(
        self,
        request: ResearchCreateRequest,
        sources: list[ResearchSource],
    ) -> ResearchReport:
        primary = sources[0]

        return ResearchReport(
            topic=request.topic,
            summary="A verified synthetic research summary.",
            findings=[
                "The workflow retained normalized evidence.",
                "Citations resolve to evaluated sources.",
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


def test_research_workflow_executes_all_lifecycle_stages() -> None:
    statuses: list[ResearchStatus] = []

    workflow = ResearchWorkflow(
        planner=FakePlanner(),
        searcher=FakeSearcher(),
        writer=FakeWriter(),
    )

    report = workflow.run(
        ResearchCreateRequest(
            topic="Evidence-driven research agents",
            maximum_sources=5,
        ),
        on_status=statuses.append,
    )

    assert statuses == [
        ResearchStatus.PLANNING,
        ResearchStatus.SEARCHING,
        ResearchStatus.EVALUATING,
        ResearchStatus.WRITING,
        ResearchStatus.VERIFYING,
    ]

    assert report.topic == "Evidence-driven research agents"
    assert report.summary
    assert report.findings
    assert report.citations

    urls = [str(source.url) for source in report.sources]

    assert urls.count("https://example.com/shared") == 1
    assert len(report.sources) == 3


class EmptySearcher:
    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        request: ResearchCreateRequest,
    ) -> list[ResearchSource]:
        del query, maximum_results, request
        return []


def test_research_workflow_fails_without_evidence() -> None:
    workflow = ResearchWorkflow(
        planner=FakePlanner(),
        searcher=EmptySearcher(),
        writer=FakeWriter(),
    )

    with pytest.raises(
        ResearchWorkflowError,
        match="without usable evidence",
    ):
        workflow.run(
            ResearchCreateRequest(
                topic="Research without evidence",
            )
        )


class InvalidCitationWriter:
    def write(
        self,
        request: ResearchCreateRequest,
        sources: list[ResearchSource],
    ) -> ResearchReport:
        return ResearchReport(
            topic=request.topic,
            summary="Invalid report.",
            findings=["Unsupported citation."],
            citations=[
                ResearchCitation(
                    source_id="src_missing",
                    title="Missing source",
                    url="https://example.com/missing",
                )
            ],
            sources=sources,
        )


def test_research_workflow_rejects_unknown_citation() -> None:
    workflow = ResearchWorkflow(
        planner=FakePlanner(),
        searcher=FakeSearcher(),
        writer=InvalidCitationWriter(),
    )

    with pytest.raises(
        ResearchWorkflowError,
        match="Unknown citation source",
    ):
        workflow.run(
            ResearchCreateRequest(
                topic="Citation verification",
                maximum_sources=5,
            )
        )
