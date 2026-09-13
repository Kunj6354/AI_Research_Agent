from __future__ import annotations

import json
import sys

from research_agent.core.config import get_settings
from research_agent.integrations.provider_factory import (
    build_provider_bundle,
    get_provider_readiness,
)
from research_agent.models.research import ResearchCreateRequest


def main() -> int:
    settings = get_settings()
    readiness = get_provider_readiness(settings)

    print(
        json.dumps(
            readiness.model_dump(),
            indent=2,
        )
    )

    if not readiness.ready:
        print(
            "LIVE_PROVIDER_ACCEPTANCE=SKIPPED reason=provider_configuration_incomplete"
        )
        return 2

    bundle = build_provider_bundle(settings)

    statuses: list[str] = []

    report = bundle.workflow.run(
        ResearchCreateRequest(
            topic=(
                "What are the main engineering tradeoffs "
                "of evidence-grounded AI research systems?"
            ),
            depth="quick",
            maximum_sources=5,
        ),
        on_status=lambda status: statuses.append(status.value),
    )

    print("LIFECYCLE=" + ",".join(statuses))

    print("SUMMARY=" + report.summary)

    print("FINDINGS=" + str(len(report.findings)))

    print("SOURCES=" + str(len(report.sources)))

    print("CITATIONS=" + str(len(report.citations)))

    assert report.summary
    assert report.findings
    assert report.sources
    assert report.citations

    print("LIVE_PROVIDER_ACCEPTANCE=PASS")

    return 0


if __name__ == "__main__":
    sys.exit(main())
