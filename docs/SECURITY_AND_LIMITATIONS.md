
Security and Known Limitations
Credentials

OpenAI and Tavily credentials are runtime secrets.

The repository contains .env.example only.

Real .env files and API keys must remain local and untracked.

The provider-readiness endpoint exposes booleans only; it never returns credential values.

External content

Search results are untrusted external content.

A retrieved page/snippet may contain incorrect information, prompt injection, malicious instructions or misleading claims.

V1 treats retrieved content as evidence text rather than executable instructions.

The synthesis prompt explicitly limits generation to supplied evidence, but this is not a complete prompt-injection defense.

Citation verification

Citation verification guarantees structural consistency between the final report and the source records collected by the backend.

It does not independently prove that:

a source is factually correct;
a source is unbiased;
a webpage has not changed;
a claim perfectly follows from the source;
the search provider returned the best available evidence.
Provider dependence

Live research depends on external OpenAI and Tavily availability, API compatibility, quotas and billing.

Automated regression tests do not require external providers.

Persistence

V1 stores jobs only in process memory.

Restarting the backend loses jobs and reports.

This is an explicit local portfolio boundary.

Execution

Research execution is synchronous.

Long research runs occupy the request until completion.

No worker queue, retries, timeout orchestration or cancellation API is implemented.

Access control

V1 does not implement:

authentication;
authorization;
user accounts;
tenant isolation;
rate limiting.

Do not expose this service directly as a public production endpoint.

Observability

Health and provider-readiness endpoints provide basic operational signals.

V1 does not implement centralized:

logs;
tracing;
metrics;
alerting.
Output review

AI-generated research may still contain errors even when citations are structurally valid.

Reports should be reviewed before use in high-stakes decisions.

Data privacy

Research topics and provider prompts may be sent to external services during live execution.

Do not submit confidential or sensitive information unless the external-provider data handling is appropriate for that use case.
