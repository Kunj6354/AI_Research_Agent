from dataclasses import dataclass

from research_agent.core.config import Settings, get_settings
from research_agent.integrations.clients import (
    build_openai_client,
    build_tavily_client,
)
from research_agent.integrations.research_providers import (
    OpenAIResearchPlanner,
    OpenAIResearchWriter,
    TavilyResearchSearcher,
)
from research_agent.models.research import ProviderReadinessResponse
from research_agent.workflows.research_workflow import ResearchWorkflow


@dataclass(frozen=True, slots=True)
class ProviderBundle:
    workflow: ResearchWorkflow


def get_provider_readiness(
    settings: Settings | None = None,
) -> ProviderReadinessResponse:
    """Return provider configuration state without exposing secrets."""

    resolved = settings or get_settings()

    openai_configured = resolved.openai_api_key is not None
    openai_model_configured = bool(resolved.openai_model)
    tavily_configured = resolved.tavily_api_key is not None

    return ProviderReadinessResponse(
        openai_configured=openai_configured,
        openai_model_configured=openai_model_configured,
        tavily_configured=tavily_configured,
        ready=(openai_configured and openai_model_configured and tavily_configured),
    )


def build_provider_bundle(
    settings: Settings,
) -> ProviderBundle:
    """Build the real externally-backed research workflow."""

    openai_client = build_openai_client(settings)
    tavily_client = build_tavily_client(settings)

    workflow = ResearchWorkflow(
        planner=OpenAIResearchPlanner(
            openai_client,
            settings,
        ),
        searcher=TavilyResearchSearcher(
            tavily_client,
            settings,
        ),
        writer=OpenAIResearchWriter(
            openai_client,
            settings,
        ),
    )

    return ProviderBundle(
        workflow=workflow,
    )


def get_provider_bundle() -> ProviderBundle:
    """Build a provider bundle from current application settings."""

    return build_provider_bundle(get_settings())
