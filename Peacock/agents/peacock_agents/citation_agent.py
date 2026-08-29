"""Citation Agent — turns Citation Gap Engine output into concrete tasks."""

from __future__ import annotations

from citation_intelligence.models import CitationGapReport

from peacock_agents.models import AgentResult, AgentTask


def run_citation_agent(report: CitationGapReport) -> AgentResult:
    tasks = [
        AgentTask(
            title=f"Close citation gap vs. {gap.cited_domain}",
            detail="; ".join(gap.recommended_fix),
            priority="High" if gap.fetch_status == "fetched" else "Medium",
        )
        for gap in report.gaps
    ]
    return AgentResult(
        agent_name="Citation Agent",
        summary=f"Analysed {report.citations_analysed} of {report.citations_observed} citation(s) observed across AI platform responses.",
        findings=[f"{g.cited_domain} ({g.source_class}) cited by {', '.join(g.engine_codes)}." for g in report.gaps],
        recommendations=[fix for g in report.gaps for fix in g.recommended_fix],
        tasks=tasks,
    )
