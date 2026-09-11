# StackOre AI Research Agent

An evidence-driven autonomous research platform that plans research, searches
current web sources, evaluates evidence, generates structured reports, and
verifies citations.

## Current Status

Backend foundation completed:

- Python 3.12
- FastAPI application factory
- Environment-based configuration
- Versioned API routes
- Health endpoint
- OpenAPI documentation
- Ruff formatting and linting
- Pytest foundation tests

## Backend Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m ensurepip --upgrade --default-pip
python -m pip install -e "./backend[dev]"
Run Quality Checks
python -m compileall -q backend/src backend/tests
python -m ruff format --check backend/src backend/tests
python -m ruff check backend/src backend/tests
python -m pytest -q backend/tests
Run Backend
fastapi dev backend/src/research_agent/main.py

Backend documentation:

Swagger UI: http://127.0.0.1:8000/docs
Health API: http://127.0.0.1:8000/api/v1/health

## Current Scope Boundary

The current repository is a backend foundation rather than a completed autonomous research system.

Implemented today:

- FastAPI service and OpenAPI contract
- health API
- research-job creation and retrieval
- validated research request/status models
- in-memory research-job storage
- OpenAI and Tavily client configuration
- provider configuration safety checks
- pytest and Ruff foundation

Not yet implemented:

- LangGraph research orchestration
- live Tavily search execution
- OpenAI research/report generation
- evidence evaluation
- citation verification
- completed research reports
- durable persistence or background workers

See `docs/REMAINING_WORK.md` for the continuation plan.
