from fastapi import FastAPI

from research_agent.api.health import router as health_router
from research_agent.core.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Evidence-driven autonomous AI research platform.",
    )

    application.include_router(
        health_router,
        prefix=settings.api_v1_prefix,
    )

    return application


app = create_app()
