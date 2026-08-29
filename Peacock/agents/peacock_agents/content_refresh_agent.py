"""Content Refresh Agent — wraps the Content Decay Detector."""

from __future__ import annotations

from measurement.models import RefreshOpportunity

from peacock_agents.models import AgentResult, AgentTask


def run_content_refresh_agent(refresh_opportunities: list[RefreshOpportunity]) -> AgentResult:
    tasks = [
        AgentTask(title=f"Refresh {r.url}", detail=r.detail, priority="High")
        for r in refresh_opportunities
    ]
    return AgentResult(
        agent_name="Content Refresh Agent",
        summary=(
            f"Detected {len(refresh_opportunities)} page(s) with declining scores across snapshots."
            if refresh_opportunities
            else "No content decay detected yet — this requires at least two snapshots of a page over time."
        ),
        findings=[r.detail for r in refresh_opportunities],
        recommendations=[r.recommended_action for r in refresh_opportunities],
        tasks=tasks,
    )
