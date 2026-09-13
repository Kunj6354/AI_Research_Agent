from datetime import date, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, HttpUrl, model_validator


class ResearchDepth(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ResearchStatus(StrEnum):
    QUEUED = "queued"
    PLANNING = "planning"
    SEARCHING = "searching"
    EVALUATING = "evaluating"
    WRITING = "writing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchTimeRange(BaseModel):
    from_date: date | None = None
    to_date: date | None = None

    @model_validator(mode="after")
    def validate_date_order(self) -> Self:
        if (
            self.from_date is not None
            and self.to_date is not None
            and self.from_date > self.to_date
        ):
            raise ValueError("from_date must not be later than to_date")

        return self


class ResearchCreateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    depth: ResearchDepth = ResearchDepth.STANDARD
    maximum_sources: int = Field(default=15, ge=5, le=50)
    time_range: ResearchTimeRange | None = None


class ResearchPlan(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=10)


class ResearchSource(BaseModel):
    source_id: str
    title: str = Field(min_length=1)
    url: HttpUrl
    content: str = Field(min_length=1)
    relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)


class ResearchCitation(BaseModel):
    source_id: str
    title: str
    url: HttpUrl


class ResearchReport(BaseModel):
    topic: str
    summary: str = Field(min_length=1)
    findings: list[str] = Field(min_length=1)
    citations: list[ResearchCitation]
    sources: list[ResearchSource]


class ResearchJobResponse(BaseModel):
    research_id: str
    topic: str
    depth: ResearchDepth
    maximum_sources: int
    status: ResearchStatus
    created_at: datetime
    updated_at: datetime
    report: ResearchReport | None = None
    error: str | None = None


class ProviderReadinessResponse(BaseModel):
    openai_configured: bool
    openai_model_configured: bool
    tavily_configured: bool
    ready: bool
