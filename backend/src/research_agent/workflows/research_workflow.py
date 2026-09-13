from collections.abc import Callable
from dataclasses import dataclass

from research_agent.integrations.providers import (
    ResearchPlanner,
    ResearchSearcher,
    ResearchWriter,
)
from research_agent.models.research import (
    ResearchCreateRequest,
    ResearchReport,
    ResearchSource,
    ResearchStatus,
)

StatusCallback = Callable[[ResearchStatus], None]


class ResearchWorkflowError(RuntimeError):
    """Raised when a research workflow cannot produce a valid report."""


@dataclass(slots=True)
class ResearchWorkflow:
    """Execute one bounded evidence-driven research workflow."""

    planner: ResearchPlanner
    searcher: ResearchSearcher
    writer: ResearchWriter

    def run(
        self,
        request: ResearchCreateRequest,
        *,
        on_status: StatusCallback | None = None,
    ) -> ResearchReport:
        self._emit(on_status, ResearchStatus.PLANNING)

        plan = self.planner.plan(request)

        self._emit(on_status, ResearchStatus.SEARCHING)

        raw_sources: list[ResearchSource] = []

        per_query_limit = max(
            1,
            min(
                request.maximum_sources,
                request.maximum_sources // len(plan.queries) or 1,
            ),
        )

        for query in plan.queries:
            raw_sources.extend(
                self.searcher.search(
                    query,
                    maximum_results=per_query_limit,
                    request=request,
                )
            )

        self._emit(on_status, ResearchStatus.EVALUATING)

        evaluated_sources = self._evaluate_sources(
            raw_sources,
            maximum_sources=request.maximum_sources,
        )

        if not evaluated_sources:
            raise ResearchWorkflowError("Research completed without usable evidence sources")

        self._emit(on_status, ResearchStatus.WRITING)

        report = self.writer.write(
            request,
            evaluated_sources,
        )

        self._emit(on_status, ResearchStatus.VERIFYING)

        self._verify_report(
            report,
            evaluated_sources,
        )

        return report

    @staticmethod
    def _emit(
        callback: StatusCallback | None,
        status: ResearchStatus,
    ) -> None:
        if callback is not None:
            callback(status)

    @staticmethod
    def _evaluate_sources(
        sources: list[ResearchSource],
        *,
        maximum_sources: int,
    ) -> list[ResearchSource]:
        """Deduplicate and rank normalized evidence deterministically."""

        by_url: dict[str, ResearchSource] = {}

        for source in sources:
            key = str(source.url)

            existing = by_url.get(key)

            if existing is None:
                by_url[key] = source
                continue

            existing_score = (
                existing.relevance_score if existing.relevance_score is not None else 0.0
            )
            candidate_score = source.relevance_score if source.relevance_score is not None else 0.0

            if candidate_score > existing_score:
                by_url[key] = source

        ranked = sorted(
            by_url.values(),
            key=lambda item: item.relevance_score if item.relevance_score is not None else 0.0,
            reverse=True,
        )

        return ranked[:maximum_sources]

    @staticmethod
    def _verify_report(
        report: ResearchReport,
        evaluated_sources: list[ResearchSource],
    ) -> None:
        """Ensure final citations resolve to evidence supplied to the writer."""

        allowed_sources = {source.source_id: source for source in evaluated_sources}

        report_source_ids = {source.source_id for source in report.sources}

        if not report_source_ids:
            raise ResearchWorkflowError("Research report contains no sources")

        unknown_report_sources = report_source_ids - set(allowed_sources)

        if unknown_report_sources:
            raise ResearchWorkflowError(
                "Research report contains sources that were not part of the evaluated evidence"
            )

        for citation in report.citations:
            source = allowed_sources.get(citation.source_id)

            if source is None:
                raise ResearchWorkflowError(f"Unknown citation source: {citation.source_id}")

            if citation.source_id not in report_source_ids:
                raise ResearchWorkflowError(
                    f"Citation source missing from report sources: {citation.source_id}"
                )

            if str(citation.url) != str(source.url):
                raise ResearchWorkflowError(
                    f"Citation URL mismatch for source: {citation.source_id}"
                )
