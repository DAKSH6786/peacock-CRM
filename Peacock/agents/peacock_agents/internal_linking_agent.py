"""Internal Linking Agent — flags orphan/under-linked pages from real crawl evidence."""

from __future__ import annotations

from site_intelligence.models import SiteIntelligenceReport

from peacock_agents.models import AgentResult, AgentTask


def run_internal_linking_agent(report: SiteIntelligenceReport) -> AgentResult:
    orphan_pages = [
        p for p in report.pages if any("orphan" in e.lower() or "inbound" in e.lower() for e in p.evidence_found)
    ]
    tasks = [
        AgentTask(
            title=f"Add internal links to {p.url}",
            detail="Page has no (or very few) inbound internal links from the crawled set.",
            priority="Medium",
        )
        for p in orphan_pages
    ]
    return AgentResult(
        agent_name="Internal Linking Agent",
        summary=f"Found {len(orphan_pages)} page(s) with weak internal-link coverage out of {len(report.pages)} crawled.",
        findings=[p.url for p in orphan_pages],
        recommendations=["Add contextual internal links from topically related pages to each orphan candidate."],
        tasks=tasks,
    )
