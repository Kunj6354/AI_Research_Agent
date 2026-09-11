# AI Research Agent — Remaining Work

## Current verified milestone

The repository currently provides a verified FastAPI backend foundation for an AI research system.

Implemented:

- FastAPI application and versioned API routes;
- health endpoint;
- research-job create/retrieve API;
- validated research request models;
- research lifecycle/status model;
- in-memory research-job storage;
- OpenAI client configuration;
- Tavily client configuration;
- fail-closed provider configuration;
- OpenAPI documentation;
- pytest and Ruff foundation.

## Important limitation

The current repository does not yet execute autonomous research.

Research jobs are created with status `queued` and remain in the in-memory foundation service.

The following workflow stages are modeled or described but are not operational:

- planning;
- searching;
- evaluating;
- writing;
- verifying.

## Future completion work

When the project is resumed:

1. implement the LangGraph state/workflow;
2. implement research-plan generation;
3. execute Tavily searches;
4. define normalized source/evidence models;
5. implement relevance and evidence-quality evaluation;
6. implement OpenAI-based synthesis;
7. implement citation/source verification;
8. expose completed research reports through the API;
9. add durable persistence;
10. add asynchronous/background research execution;
11. implement retries, cancellation and failure handling;
12. add mocked provider integration tests;
13. add real-provider acceptance testing using private local credentials;
14. create a portfolio-grade end-to-end demonstration;
15. complete the C01-C26 project-completion contract.

## Preservation rule

Do not implement the missing autonomous workflow during the current Kunj Vault milestone-preservation pass.
