from functools import lru_cache

from openai import OpenAI
from tavily import TavilyClient

from research_agent.core.config import Settings, get_settings


class MissingIntegrationConfiguration(RuntimeError):
    """Raised when an external integration is used without configuration."""


def build_openai_client(settings: Settings) -> OpenAI:
    """Build an OpenAI client from validated application settings."""

    if settings.openai_api_key is None:
        raise MissingIntegrationConfiguration("OPENAI_API_KEY is not configured")

    return OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
    )


def build_tavily_client(settings: Settings) -> TavilyClient:
    """Build a Tavily client from validated application settings."""

    if settings.tavily_api_key is None:
        raise MissingIntegrationConfiguration("TAVILY_API_KEY is not configured")

    return TavilyClient(
        api_key=settings.tavily_api_key.get_secret_value(),
    )


@lru_cache
def get_openai_client() -> OpenAI:
    """Return the application-wide OpenAI client."""

    return build_openai_client(get_settings())


@lru_cache
def get_tavily_client() -> TavilyClient:
    """Return the application-wide Tavily client."""

    return build_tavily_client(get_settings())
