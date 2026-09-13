# AI Research Agent

AI Research Agent is an evidence-driven research backend that turns a research topic into a structured, source-grounded report.

Canonical project ID: **CAN-008**

## What It Does

The backend implements a bounded research workflow:

```text
research request
    -> planning
    -> web search
    -> evidence normalization
    -> relevance ranking / deduplication
    -> report synthesis
    -> citation verification
    -> completed structured report
The public API supports research-job creation, execution and retrieval.

External integrations:

OpenAI for research planning and report synthesis
Tavily for current web-search retrieval

The automated test suite uses deterministic mocked providers and does not require paid API calls.

Architecture
FastAPI API
    |
    +-- Research Job Service
    |       |
    |       +-- queued / lifecycle / failed / completed state
    |
    +-- Research Workflow
            |
            +-- Planner
            +-- Searcher
            +-- Evidence evaluation
            +-- Writer
            +-- Citation verification

Provider interfaces keep orchestration independent from concrete OpenAI and Tavily clients.

The backend—not the language model—owns citation URLs. The synthesis model returns source IDs, which are resolved against normalized evidence records and verified before a report is accepted.

Research Lifecycle

Supported statuses:

queued
planning
searching
evaluating
writing
verifying
completed
failed
cancelled

V1 execution is synchronous.

API

Local base URL:

http://127.0.0.1:8000

Important routes:

GET  /api/v1/health
GET  /api/v1/research/providers/readiness
POST /api/v1/research
POST /api/v1/research/{research_id}/run
GET  /api/v1/research/{research_id}

Interactive OpenAPI documentation:

http://127.0.0.1:8000/docs
Setup

Python 3.12+ is required.

From the repository root:

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".\backend[dev]"

Create a private .env only when real providers are needed.

Use .env.example as the template.

Never commit API keys.

Required live-provider variables:

OPENAI_API_KEY
OPENAI_MODEL
TAVILY_API_KEY

Optional Tavily settings:

TAVILY_SEARCH_DEPTH
TAVILY_MAX_RESULTS
Run
.\.venv\Scripts\python.exe -m fastapi dev backend/src/research_agent/main.py
Quality Checks
.\.venv\Scripts\python.exe -m ruff format --check backend/src backend/tests scripts
.\.venv\Scripts\python.exe -m ruff check backend/src backend/tests scripts
.\.venv\Scripts\python.exe -m pytest -q backend/tests
.\.venv\Scripts\python.exe -m compileall -q backend/src backend/tests scripts
.\.venv\Scripts\python.exe -m pip check
Deterministic Demo

The repository includes a provider-free demonstration of the full research lifecycle:

.\.venv\Scripts\python.exe .\scripts\deterministic_demo.py

The demo validates:

job creation;
workflow execution;
evidence collection;
structured report creation;
source retention;
citation verification;
completed state.
Optional Live Provider Acceptance

When valid private credentials are configured:

.\.venv\Scripts\python.exe .\scripts\live_provider_acceptance.py

If provider configuration is absent, the script exits safely without making an external request.

V1 Scope Boundary

Implemented:

FastAPI research API;
validated research requests;
in-memory job lifecycle;
OpenAI planning adapter;
Tavily search adapter;
normalized evidence;
deterministic relevance ranking and URL deduplication;
OpenAI synthesis adapter;
backend-authoritative citation mapping;
citation verification;
controlled provider readiness;
controlled failure state;
deterministic unit/integration/API tests;
deterministic portfolio demo;
optional real-provider acceptance harness.

Not included in V1:

persistent database storage;
distributed/background workers;
authentication or multi-tenancy;
frontend application;
autonomous recursive sub-agents;
production hosting;
cancellation endpoint;
retry scheduler;
centralized observability.

These are deliberate future-product extensions, not incomplete V1 requirements.

Portfolio Position

This project demonstrates:

backend API engineering;
AI-provider integration;
evidence-grounded workflow architecture;
structured LLM output handling;
source normalization;
hallucinated-citation prevention;
deterministic testing around external AI systems;
explicit operational and security boundaries.

See docs/ARCHITECTURE.md, docs/PORTFOLIO_CASE_STUDY.md,
docs/SECURITY_AND_LIMITATIONS.md, and docs/COMPLETION_CLOSURE.md.
