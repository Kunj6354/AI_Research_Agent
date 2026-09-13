from research_agent.models.research import (
    ResearchCitation,
    ResearchCreateRequest,
    ResearchPlan,
    ResearchReport,
    ResearchSource,
    ResearchStatus,
)
from research_agent.services.research_service import InMemoryResearchService
from research_agent.workflows.research_workflow import ResearchWorkflow


class DemoPlanner:
    def plan(
        self,
        request: ResearchCreateRequest,
    ) -> ResearchPlan:
        return ResearchPlan(
            queries=[
                f"{request.topic} architecture",
                f"{request.topic} evidence grounding",
            ]
        )


class DemoSearcher:
    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        request: ResearchCreateRequest,
    ) -> list[ResearchSource]:
        del request

        candidates = [
            ResearchSource(
                source_id="src_architecture",
                title="Research-system architecture reference",
                url="https://example.com/research-architecture",
                content=(
                    "Evidence-driven research systems separate "
                    "planning, retrieval, synthesis and verification."
                ),
                relevance_score=0.96,
            ),
            ResearchSource(
                source_id="src_grounding",
                title="Evidence-grounding reference",
                url="https://example.com/evidence-grounding",
                content=(
                    "Citation identifiers should resolve to "
                    "retrieved source records rather than model-created URLs."
                ),
                relevance_score=0.94,
            ),
        ]

        if "architecture" in query:
            candidates.reverse()

        return candidates[:maximum_results]


class DemoWriter:
    def write(
        self,
        request: ResearchCreateRequest,
        sources: list[ResearchSource],
    ) -> ResearchReport:
        citations = [
            ResearchCitation(
                source_id=source.source_id,
                title=source.title,
                url=source.url,
            )
            for source in sources
        ]

        return ResearchReport(
            topic=request.topic,
            summary=(
                "A bounded research workflow can separate planning, "
                "source retrieval, synthesis and citation verification."
            ),
            findings=[
                (
                    "Search results are normalized before synthesis so "
                    "the backend retains source authority."
                ),
                (
                    "Final citations are checked against evaluated "
                    "evidence instead of accepting arbitrary model URLs."
                ),
            ],
            citations=citations,
            sources=sources,
        )


def main() -> None:
    service = InMemoryResearchService()

    request = ResearchCreateRequest(
        topic="Evidence-grounded AI research systems",
        depth="quick",
        maximum_sources=5,
    )

    job = service.create_job(request)

    print("CREATED", job.research_id, job.status.value)

    workflow = ResearchWorkflow(
        planner=DemoPlanner(),
        searcher=DemoSearcher(),
        writer=DemoWriter(),
    )

    completed = service.run_job(
        job.research_id,
        workflow,
    )

    assert completed is not None
    assert completed.status is ResearchStatus.COMPLETED
    assert completed.report is not None
    assert completed.error is None

    report = completed.report

    print("STATUS", completed.status.value)
    print("TOPIC", report.topic)
    print("SUMMARY", report.summary)
    print("FINDINGS", len(report.findings))
    print("SOURCES", len(report.sources))
    print("CITATIONS", len(report.citations))

    for citation in report.citations:
        print(
            "CITATION",
            citation.source_id,
            citation.title,
            citation.url,
        )

    print("DETERMINISTIC_DEMO=PASS")


if __name__ == "__main__":
    main()
