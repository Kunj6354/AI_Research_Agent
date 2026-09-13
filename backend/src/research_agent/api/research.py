from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from research_agent.integrations.clients import MissingIntegrationConfiguration
from research_agent.integrations.provider_factory import (
    ProviderBundle,
    get_provider_bundle,
    get_provider_readiness,
)
from research_agent.models.research import (
    ProviderReadinessResponse,
    ResearchCreateRequest,
    ResearchJobResponse,
)
from research_agent.services.research_service import (
    InMemoryResearchService,
    ResearchJobStateError,
    get_research_service,
)

router = APIRouter(
    prefix="/research",
    tags=["research"],
)

ResearchServiceDependency = Annotated[
    InMemoryResearchService,
    Depends(get_research_service),
]


def resolve_provider_bundle() -> ProviderBundle:
    """Resolve configured providers or return a controlled service error."""

    try:
        return get_provider_bundle()
    except (MissingIntegrationConfiguration, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Research providers are not ready: {exc}",
        ) from exc


ProviderBundleDependency = Annotated[
    ProviderBundle,
    Depends(resolve_provider_bundle),
]


@router.get(
    "/providers/readiness",
    response_model=ProviderReadinessResponse,
)
def provider_readiness() -> ProviderReadinessResponse:
    """Expose non-secret provider configuration readiness."""

    return get_provider_readiness()


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


@router.post(
    "/{research_id}/run",
    response_model=ResearchJobResponse,
)
def run_research_job(
    research_id: str,
    service: ResearchServiceDependency,
    providers: ProviderBundleDependency,
) -> ResearchJobResponse:
    """Execute a queued research job synchronously."""

    try:
        job = service.run_job(
            research_id,
            providers.workflow,
        )
    except ResearchJobStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research job not found",
        )

    return job


@router.get(
    "/{research_id}",
    response_model=ResearchJobResponse,
)
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
