"""Competitor Agent — explains WHY a competitor is winning, not just the numbers."""

from __future__ import annotations

from site_intelligence.models import CompetitorComparison

from peacock_agents.models import AgentResult, AgentTask


def run_competitor_agent(comparison: CompetitorComparison) -> AgentResult:
    if not comparison.available:
        return AgentResult(
            agent_name="Competitor Agent",
            summary="No competitor URL was supplied for a direct crawl-based comparison.",
            findings=[comparison.reason_unavailable or "Data unavailable."],
            recommendations=["Supply a competitor URL to enable a direct content/entity/topic comparison."],
        )

    tasks = [
        AgentTask(
            title="Close competitor content gap",
            detail=reason,
            priority="High",
        )
        for reason in comparison.why_competitor_is_winning
    ]
    return AgentResult(
        agent_name="Competitor Agent",
        summary=f"Compared against {comparison.competitor_url} using real crawled content from both sites.",
        findings=[
            comparison.entity_coverage,
            comparison.content_coverage,
            comparison.structured_data,
            comparison.question_coverage,
            comparison.ai_mentions,
        ],
        recommendations=comparison.why_competitor_is_winning,
        tasks=tasks,
    )
