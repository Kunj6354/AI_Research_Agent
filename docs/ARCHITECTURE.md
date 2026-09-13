AI Research Agent Architecture
Product boundary

AI Research Agent V1 is a local FastAPI research backend.

It accepts a bounded research request, executes planning/search/evidence/synthesis/verification stages and returns a structured report.

V1 is synchronous and in-memory.

Authority boundaries
Backend authority

Python owns:

job state;
source records;
relevance ordering;
URL deduplication;
citation URL resolution;
citation verification;
provider configuration readiness;
failure handling.
LLM authority

OpenAI may produce:

search-query planning;
report summary;
report findings;
selected source identifiers.

It does not have authority to create trusted citation URLs.

Search-provider authority

Tavily supplies raw search result:

title;
URL;
content/snippet;
relevance score.

The backend normalizes this into ResearchSource.

Workflow
ResearchCreateRequest
       |
       v
Research Job [queued]
       |
       v
Planner [planning]
       |
       v
ResearchPlan
       |
       v
Searcher [searching]
       |
       v
ResearchSource[]
       |
       v
Deduplicate + Rank [evaluating]
       |
       v
Writer [writing]
       |
       v
ResearchReport candidate
       |
       v
Citation verification [verifying]
       |
       +------ invalid ------> failed
       |
       v
completed
Provider abstraction

The workflow depends on three protocols:

ResearchPlanner
ResearchSearcher
ResearchWriter

Production adapters are:

OpenAIResearchPlanner
TavilyResearchSearcher
OpenAIResearchWriter

Tests use deterministic fake implementations.

This allows orchestration to be tested without network access or paid-provider credentials.

Evidence handling

Every search result is converted into a normalized source with a deterministic backend source identifier.

Results are deduplicated by URL.

Where duplicate URLs exist, the highest relevance score wins.

Sources are ordered by relevance and bounded by the request's maximum_sources.

Citation integrity

The writer receives evaluated source records.

The model returns source IDs rather than authoritative URLs.

Python then maps cited source IDs to source title/URL records.

The workflow rejects:

unknown citation IDs;
report sources not present in evaluated evidence;
citation URLs that do not match the authoritative evidence source;
reports without usable evidence.

This reduces one common failure mode of LLM research systems: invented or mismatched citations.

Job storage

V1 uses process-local in-memory storage protected by an RLock.

This is suitable for the portfolio/local V1 boundary.

It is not durable across process restarts and is not intended for horizontally scaled deployment.

Execution model

POST /research/{id}/run performs synchronous execution.

The request remains open until research completes or fails.

Background queues and worker processes are intentionally outside V1.

Future extension boundary

A production evolution could add:

PostgreSQL persistence;
async task queue;
retries and cancellation;
authentication;
multi-tenant isolation;
tracing/metrics;
rate limiting;
richer evidence scoring;
recursive/decomposed research;
frontend interface.

Those are extensions to the completed V1 architecture rather than requirements for portfolio closure.
