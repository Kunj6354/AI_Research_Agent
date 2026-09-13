import hashlib
import json
from typing import Any

from openai import OpenAI
from tavily import TavilyClient

from research_agent.core.config import Settings
from research_agent.models.research import (
    ResearchCitation,
    ResearchCreateRequest,
    ResearchPlan,
    ResearchReport,
    ResearchSource,
)


class ProviderResponseError(RuntimeError):
    """Raised when an external provider returns unusable structured data."""


class OpenAIResearchPlanner:
    """Generate a bounded research search plan with OpenAI."""

    def __init__(
        self,
        client: OpenAI,
        settings: Settings,
    ) -> None:
        if not settings.openai_model:
            raise ValueError("OPENAI_MODEL is not configured")

        self._client = client
        self._model = settings.openai_model

    def plan(
        self,
        request: ResearchCreateRequest,
    ) -> ResearchPlan:
        query_target = {
            "quick": 2,
            "standard": 4,
            "deep": 6,
        }[request.depth.value]

        time_range_text = _format_time_range(request)

        prompt = f"""
You are the planning stage of an evidence-driven research system.

Research topic:
{request.topic}

Depth:
{request.depth.value}

Requested time range:
{time_range_text}

Generate exactly {query_target} distinct web-search queries.

Requirements:
- queries must directly support answering the topic;
- cover complementary aspects rather than trivial wording variants;
- prefer precise searchable language;
- do not answer the research question;
- return JSON only.

Required JSON shape:
{{
  "queries": [
    "query one",
    "query two"
  ]
}}
""".strip()

        response = self._client.responses.create(
            model=self._model,
            input=prompt,
        )

        payload = _load_json_response(
            response.output_text,
            provider_stage="planning",
        )

        queries = payload.get("queries")

        if not isinstance(queries, list):
            raise ProviderResponseError("Planning response does not contain a queries list")

        normalized_queries = [str(query).strip() for query in queries if str(query).strip()]

        if len(normalized_queries) != query_target:
            raise ProviderResponseError(
                f"Planning response returned {len(normalized_queries)} "
                f"queries; expected {query_target}"
            )

        return ResearchPlan(
            queries=normalized_queries,
        )


class TavilyResearchSearcher:
    """Search Tavily and normalize result records into research evidence."""

    def __init__(
        self,
        client: TavilyClient,
        settings: Settings,
    ) -> None:
        self._client = client
        self._search_depth = settings.tavily_search_depth
        self._configured_max_results = settings.tavily_max_results

    def search(
        self,
        query: str,
        *,
        maximum_results: int,
        request: ResearchCreateRequest,
    ) -> list[ResearchSource]:
        requested_results = min(
            maximum_results,
            self._configured_max_results,
        )

        search_kwargs: dict[str, Any] = {
            "query": query,
            "search_depth": self._search_depth,
            "max_results": requested_results,
        }

        if request.time_range is not None:
            if request.time_range.from_date is not None:
                search_kwargs["start_date"] = request.time_range.from_date.isoformat()

            if request.time_range.to_date is not None:
                search_kwargs["end_date"] = request.time_range.to_date.isoformat()

        payload = self._client.search(**search_kwargs)

        raw_results = payload.get("results", [])

        if not isinstance(raw_results, list):
            raise ProviderResponseError("Tavily response does not contain a results list")

        sources: list[ResearchSource] = []

        for result in raw_results:
            if not isinstance(result, dict):
                continue

            title = str(result.get("title") or "").strip()
            url = str(result.get("url") or "").strip()
            content = str(result.get("content") or "").strip()

            if not title or not url or not content:
                continue

            score = result.get("score")

            relevance_score: float | None = None

            if isinstance(score, int | float):
                relevance_score = max(
                    0.0,
                    min(1.0, float(score)),
                )

            sources.append(
                ResearchSource(
                    source_id=_source_id_from_url(url),
                    title=title,
                    url=url,
                    content=content,
                    relevance_score=relevance_score,
                )
            )

        return sources


class OpenAIResearchWriter:
    """Synthesize evaluated evidence into a structured report."""

    def __init__(
        self,
        client: OpenAI,
        settings: Settings,
    ) -> None:
        if not settings.openai_model:
            raise ValueError("OPENAI_MODEL is not configured")

        self._client = client
        self._model = settings.openai_model

    def write(
        self,
        request: ResearchCreateRequest,
        sources: list[ResearchSource],
    ) -> ResearchReport:
        evidence = "\n\n".join(_format_source_for_prompt(source) for source in sources)

        prompt = f"""
You are the synthesis stage of an evidence-driven research system.

Research topic:
{request.topic}

Research depth:
{request.depth.value}

You must use only the supplied evidence below.

EVIDENCE
========
{evidence}
========

Produce a concise research report.

Rules:
- do not introduce unsupported factual claims;
- findings must be grounded in the supplied evidence;
- cited_source_ids may contain only source IDs shown above;
- do not invent URLs;
- do not invent source IDs;
- use multiple sources where useful;
- if evidence is limited, state that limitation;
- return JSON only.

Required JSON shape:
{{
  "summary": "overall evidence-grounded summary",
  "findings": [
    "finding one",
    "finding two"
  ],
  "cited_source_ids": [
    "src_..."
  ]
}}
""".strip()

        response = self._client.responses.create(
            model=self._model,
            input=prompt,
        )

        payload = _load_json_response(
            response.output_text,
            provider_stage="writing",
        )

        summary = str(payload.get("summary") or "").strip()
        findings = payload.get("findings")
        cited_source_ids = payload.get("cited_source_ids")

        if not summary:
            raise ProviderResponseError("Writing response contains no summary")

        if not isinstance(findings, list):
            raise ProviderResponseError("Writing response contains no findings list")

        normalized_findings = [str(finding).strip() for finding in findings if str(finding).strip()]

        if not normalized_findings:
            raise ProviderResponseError("Writing response contains no usable findings")

        if not isinstance(cited_source_ids, list):
            raise ProviderResponseError("Writing response contains no cited_source_ids list")

        source_by_id = {source.source_id: source for source in sources}

        normalized_citation_ids: list[str] = []

        for source_id_value in cited_source_ids:
            source_id = str(source_id_value).strip()

            if not source_id:
                continue

            if source_id not in source_by_id:
                raise ProviderResponseError(f"Writer cited unknown source ID: {source_id}")

            if source_id not in normalized_citation_ids:
                normalized_citation_ids.append(source_id)

        if not normalized_citation_ids:
            raise ProviderResponseError("Writing response contains no valid citations")

        citations = [
            ResearchCitation(
                source_id=source_id,
                title=source_by_id[source_id].title,
                url=source_by_id[source_id].url,
            )
            for source_id in normalized_citation_ids
        ]

        return ResearchReport(
            topic=request.topic,
            summary=summary,
            findings=normalized_findings,
            citations=citations,
            sources=sources,
        )


def _source_id_from_url(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]

    return f"src_{digest}"


def _format_time_range(
    request: ResearchCreateRequest,
) -> str:
    if request.time_range is None:
        return "No explicit time range"

    from_date = (
        request.time_range.from_date.isoformat()
        if request.time_range.from_date is not None
        else "open"
    )
    to_date = (
        request.time_range.to_date.isoformat() if request.time_range.to_date is not None else "open"
    )

    return f"{from_date} to {to_date}"


def _format_source_for_prompt(
    source: ResearchSource,
) -> str:
    return (
        f"Source ID: {source.source_id}\n"
        f"Title: {source.title}\n"
        f"URL: {source.url}\n"
        f"Relevance: {source.relevance_score}\n"
        f"Content:\n{source.content}"
    )


def _load_json_response(
    text: str,
    *,
    provider_stage: str,
) -> dict[str, Any]:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ProviderResponseError(f"{provider_stage} provider returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise ProviderResponseError(f"{provider_stage} provider returned a non-object JSON value")

    return payload
