from datetime import UTC, datetime
from functools import lru_cache
from threading import RLock
from uuid import uuid4

from research_agent.models.research import (
    ResearchCreateRequest,
    ResearchJobResponse,
    ResearchStatus,
)
from research_agent.workflows.research_workflow import ResearchWorkflow


class ResearchJobStateError(RuntimeError):
    """Raised when a research job cannot execute from its current state."""


class InMemoryResearchService:
    """Manage research jobs and their source requests in memory."""

    def __init__(self) -> None:
        self._jobs: dict[str, ResearchJobResponse] = {}
        self._requests: dict[str, ResearchCreateRequest] = {}
        self._lock = RLock()

    def create_job(
        self,
        request: ResearchCreateRequest,
    ) -> ResearchJobResponse:
        now = datetime.now(UTC)

        job = ResearchJobResponse(
            research_id=f"res_{uuid4().hex}",
            topic=request.topic,
            depth=request.depth,
            maximum_sources=request.maximum_sources,
            status=ResearchStatus.QUEUED,
            created_at=now,
            updated_at=now,
            report=None,
            error=None,
        )

        with self._lock:
            self._jobs[job.research_id] = job
            self._requests[job.research_id] = request

        return job

    def get_job(
        self,
        research_id: str,
    ) -> ResearchJobResponse | None:
        with self._lock:
            return self._jobs.get(research_id)

    def run_job(
        self,
        research_id: str,
        workflow: ResearchWorkflow,
    ) -> ResearchJobResponse | None:
        with self._lock:
            job = self._jobs.get(research_id)
            request = self._requests.get(research_id)

        if job is None or request is None:
            return None

        if job.status not in {
            ResearchStatus.QUEUED,
            ResearchStatus.FAILED,
        }:
            raise ResearchJobStateError(f"Research job cannot run from status: {job.status.value}")

        self._update_job(
            research_id,
            status=ResearchStatus.QUEUED,
            report=None,
            error=None,
        )

        def update_status(status: ResearchStatus) -> None:
            self._update_job(
                research_id,
                status=status,
            )

        try:
            report = workflow.run(
                request,
                on_status=update_status,
            )
        except Exception as exc:
            return self._update_job(
                research_id,
                status=ResearchStatus.FAILED,
                report=None,
                error=f"Research execution failed: {exc}",
            )

        return self._update_job(
            research_id,
            status=ResearchStatus.COMPLETED,
            report=report,
            error=None,
        )

    def _update_job(
        self,
        research_id: str,
        *,
        status: ResearchStatus | None = None,
        report: object = ...,
        error: object = ...,
    ) -> ResearchJobResponse:
        with self._lock:
            current = self._jobs[research_id]

            updates: dict[str, object] = {
                "updated_at": datetime.now(UTC),
            }

            if status is not None:
                updates["status"] = status

            if report is not ...:
                updates["report"] = report

            if error is not ...:
                updates["error"] = error

            updated = current.model_copy(
                update=updates,
            )

            self._jobs[research_id] = updated

            return updated


@lru_cache
def get_research_service() -> InMemoryResearchService:
    """Return the application-wide research service."""

    return InMemoryResearchService()
