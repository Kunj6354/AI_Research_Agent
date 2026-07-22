from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from research_agent.core.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str
    environment: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Report whether the backend process is operational."""

    settings = get_settings()

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )
