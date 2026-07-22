from datetime import UTC, datetime
from functools import lru_cache
from threading import RLock
from uuid import uuid4

from research_agent.models.research import (
    ResearchCreateRequest,
    ResearchJobResponse,
    ResearchStatus,
)


class InMemoryResearchService:
    """Store research jobs in memory during the foundation stage."""

    def __init__(self) -> None:
        self._jobs: dict[str, ResearchJobResponse] = {}
        self._lock = RLock()

    def create_job(self, request: ResearchCreateRequest) -> ResearchJobResponse:
        now = datetime.now(UTC)

        job = ResearchJobResponse(
            research_id=f"res_{uuid4().hex}",
            topic=request.topic,
            depth=request.depth,
            maximum_sources=request.maximum_sources,
            status=ResearchStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._jobs[job.research_id] = job

        return job

    def get_job(self, research_id: str) -> ResearchJobResponse | None:
        with self._lock:
            return self._jobs.get(research_id)


@lru_cache
def get_research_service() -> InMemoryResearchService:
    """Return the application-wide research service."""

    return InMemoryResearchService()
