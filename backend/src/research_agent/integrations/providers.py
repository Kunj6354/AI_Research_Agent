from typing import Protocol

from research_agent.models.research import (
    ResearchCreateRequest,
    ResearchPlan,
    ResearchReport,
    ResearchSource,
)


class ResearchPlanner(Protocol):
    """Generate a bounded search plan for one research request."""

    def plan(self, request: ResearchCreateRequest) -> ResearchPlan: ...


class ResearchSearcher(Protocol):
    """Search external sources and normalize them into evidence records."""

    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        request: ResearchCreateRequest,
    ) -> list[ResearchSource]: ...


class ResearchWriter(Protocol):
    """Synthesize evaluated evidence into a structured research report."""

    def write(
        self,
        request: ResearchCreateRequest,
        sources: list[ResearchSource],
    ) -> ResearchReport: ...
