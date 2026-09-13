
AI Research Agent Portfolio Case Study
Problem

A simple LLM research script can produce plausible prose while losing the connection between claims and retrieved evidence.

Citation URLs can also be invented or mismatched if the language model is treated as the authority for both analysis and provenance.

Solution

AI Research Agent separates the workflow into explicit stages:

plan research queries;
retrieve web evidence;
normalize source records;
deduplicate and rank evidence;
synthesize a structured report;
map model-selected source IDs back to backend-controlled records;
verify citation consistency before accepting the report.
Engineering decisions
Provider-independent orchestration

The core workflow depends on planner/searcher/writer protocols rather than concrete SDK classes.

This enables deterministic regression tests without API cost or network dependency.

Backend-authoritative citations

The synthesis model never receives authority to declare trusted citation URLs.

It chooses source IDs from the supplied evidence.

Python maps those IDs to normalized source records and rejects unknown or inconsistent citations.

Explicit lifecycle

Jobs expose meaningful states:

queued
planning
searching
evaluating
writing
verifying
completed / failed

This makes execution state observable and provides a clean path toward future background workers.

Fail-closed configuration

Provider readiness can be inspected without exposing secrets.

Attempting live execution without configured providers returns a controlled service-unavailable response rather than silently degrading or crashing.

Narrow V1 boundary

The project deliberately avoids adding a database, frontend, distributed queue or multi-agent architecture solely to appear more complex.

The result is a smaller system whose implemented claims can be directly demonstrated and tested.

Validation

Automated validation covers:

request validation;
research-job API;
lifecycle execution;
provider adapters;
source normalization;
date-range forwarding;
source deduplication;
evidence-empty failure;
hallucinated source-ID rejection;
citation verification;
provider readiness;
missing-provider behavior;
OpenAPI contract.

A deterministic end-to-end demo proves the complete workflow without external credentials.

An optional live-provider script is available for private acceptance using configured OpenAI and Tavily credentials.

Portfolio value

The project demonstrates practical AI engineering beyond prompt wrappers:

architecture around unreliable external systems;
deterministic tests for LLM/provider integrations;
evidence provenance;
structured model outputs;
defensive validation;
explicit failure boundaries;
honest product scope.
