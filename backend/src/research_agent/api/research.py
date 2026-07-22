from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from research_agent.models.research import ResearchCreateRequest, ResearchJobResponse
from research_agent.services.research_service import (
    InMemoryResearchService,
    get_research_service,
)

router = APIRouter(prefix="/research", tags=["research"])

ResearchServiceDependency = Annotated[
    InMemoryResearchService,
    Depends(get_research_service),
]


@router.post(
    "",
    response_model=ResearchJobResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_research_job(
    request: ResearchCreateRequest,
    service: ResearchServiceDependency,
) -> ResearchJobResponse:
    """Create a queued research job."""

    return service.create_job(request)


@router.get("/{research_id}", response_model=ResearchJobResponse)
def get_research_job(
    research_id: str,
    service: ResearchServiceDependency,
) -> ResearchJobResponse:
    """Return an existing research job."""

    job = service.get_job(research_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research job not found",
        )

    return job
