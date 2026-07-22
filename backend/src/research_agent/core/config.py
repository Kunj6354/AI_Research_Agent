from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the research-agent backend."""

    app_name: str = "StackOre AI Research Agent"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    openai_api_key: SecretStr | None = None
    openai_model: str | None = None

    tavily_api_key: SecretStr | None = None
    tavily_search_depth: Literal["basic", "advanced"] = "basic"
    tavily_max_results: int = Field(default=5, ge=1, le=20)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator(
        "openai_api_key",
        "openai_model",
        "tavily_api_key",
        mode="before",
    )
    @classmethod
    def convert_blank_values_to_none(cls, value: object) -> object:
        """Treat empty environment variables as unconfigured values."""

        if isinstance(value, str) and not value.strip():
            return None

        return value


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance."""

    return Settings()
