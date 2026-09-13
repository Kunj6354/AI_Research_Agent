from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from research_agent.core.config import Settings
from research_agent.integrations.research_providers import (
    OpenAIResearchPlanner,
    OpenAIResearchWriter,
    ProviderResponseError,
    TavilyResearchSearcher,
)
from research_agent.models.research import (
    ResearchCreateRequest,
    ResearchSource,
)


def configured_settings() -> Settings:
    return Settings(
        openai_api_key="test-openai-key",
        openai_model="test-model",
        tavily_api_key="test-tavily-key",
        tavily_search_depth="advanced",
        tavily_max_results=8,
    )


def test_openai_planner_parses_search_queries() -> None:
    client = Mock()

    client.responses.create.return_value = SimpleNamespace(
        output_text="""
        {
          "queries": [
            "research agent architecture",
            "research agent evidence"
          ]
        }
        """
    )

    settings = configured_settings()

    planner = OpenAIResearchPlanner(
        client,
        settings,
    )

    plan = planner.plan(
        ResearchCreateRequest(
            topic="Research agents",
            depth="quick",
        )
    )

    assert plan.queries == [
        "research agent architecture",
        "research agent evidence",
    ]

    client.responses.create.assert_called_once()

    call = client.responses.create.call_args

    assert call.kwargs["model"] == "test-model"
    assert "Research agents" in call.kwargs["input"]


def test_openai_planner_rejects_wrong_query_count() -> None:
    client = Mock()

    client.responses.create.return_value = SimpleNamespace(output_text='{"queries": ["only one"]}')

    planner = OpenAIResearchPlanner(
        client,
        configured_settings(),
    )

    with pytest.raises(
        ProviderResponseError,
        match="expected 2",
    ):
        planner.plan(
            ResearchCreateRequest(
                topic="Research agents",
                depth="quick",
            )
        )


def test_tavily_searcher_normalizes_provider_results() -> None:
    client = Mock()

    client.search.return_value = {
        "results": [
            {
                "title": "Evidence source",
                "url": "https://example.com/source",
                "content": "Useful evidence.",
                "score": 0.91,
            },
            {
                "title": "",
                "url": "https://example.com/invalid",
                "content": "Missing title.",
                "score": 0.5,
            },
        ]
    }

    searcher = TavilyResearchSearcher(
        client,
        configured_settings(),
    )

    sources = searcher.search(
        "research query",
        maximum_results=5,
        request=ResearchCreateRequest(
            topic="Research agents",
        ),
    )

    assert len(sources) == 1

    source = sources[0]

    assert source.source_id.startswith("src_")
    assert source.title == "Evidence source"
    assert str(source.url) == "https://example.com/source"
    assert source.content == "Useful evidence."
    assert source.relevance_score == 0.91

    call = client.search.call_args

    assert call.kwargs["query"] == "research query"
    assert call.kwargs["search_depth"] == "advanced"
    assert call.kwargs["max_results"] == 5


def test_tavily_searcher_forwards_date_range() -> None:
    client = Mock()
    client.search.return_value = {"results": []}

    searcher = TavilyResearchSearcher(
        client,
        configured_settings(),
    )

    request = ResearchCreateRequest.model_validate(
        {
            "topic": "Research agents",
            "time_range": {
                "from_date": "2025-01-01",
                "to_date": "2026-01-01",
            },
        }
    )

    searcher.search(
        "research query",
        maximum_results=5,
        request=request,
    )

    call = client.search.call_args

    assert call.kwargs["start_date"] == "2025-01-01"
    assert call.kwargs["end_date"] == "2026-01-01"


def test_openai_writer_maps_source_ids_to_authoritative_citations() -> None:
    client = Mock()

    client.responses.create.return_value = SimpleNamespace(
        output_text="""
        {
          "summary": "Evidence supports the main conclusion.",
          "findings": [
            "Finding one",
            "Finding two"
          ],
          "cited_source_ids": [
            "src_one"
          ]
        }
        """
    )

    writer = OpenAIResearchWriter(
        client,
        configured_settings(),
    )

    source = ResearchSource(
        source_id="src_one",
        title="Authoritative source",
        url="https://example.com/authoritative",
        content="Evidence content.",
        relevance_score=0.98,
    )

    report = writer.write(
        ResearchCreateRequest(
            topic="Research agents",
        ),
        [source],
    )

    assert report.summary == ("Evidence supports the main conclusion.")

    assert report.findings == [
        "Finding one",
        "Finding two",
    ]

    assert len(report.citations) == 1
    assert report.citations[0].source_id == "src_one"
    assert report.citations[0].title == "Authoritative source"

    assert str(report.citations[0].url) == "https://example.com/authoritative"


def test_openai_writer_rejects_hallucinated_source_id() -> None:
    client = Mock()

    client.responses.create.return_value = SimpleNamespace(
        output_text="""
        {
          "summary": "Summary.",
          "findings": ["Finding"],
          "cited_source_ids": ["src_fake"]
        }
        """
    )

    writer = OpenAIResearchWriter(
        client,
        configured_settings(),
    )

    source = ResearchSource(
        source_id="src_real",
        title="Real source",
        url="https://example.com/real",
        content="Real evidence.",
        relevance_score=0.9,
    )

    with pytest.raises(
        ProviderResponseError,
        match="unknown source ID",
    ):
        writer.write(
            ResearchCreateRequest(
                topic="Research agents",
            ),
            [source],
        )


def test_openai_writer_accepts_fenced_json() -> None:
    client = Mock()

    client.responses.create.return_value = SimpleNamespace(
        output_text="""```json
{
  "summary": "Summary.",
  "findings": ["Finding"],
  "cited_source_ids": ["src_real"]
}
```"""
    )

    writer = OpenAIResearchWriter(
        client,
        configured_settings(),
    )

    source = ResearchSource(
        source_id="src_real",
        title="Real source",
        url="https://example.com/real",
        content="Real evidence.",
        relevance_score=0.9,
    )

    report = writer.write(
        ResearchCreateRequest(
            topic="Research agents",
        ),
        [source],
    )

    assert report.summary == "Summary."
