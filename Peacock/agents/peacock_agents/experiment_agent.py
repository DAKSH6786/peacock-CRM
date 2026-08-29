"""Experiment Agent — summarises running/completed experiments and suggests new ones."""

from __future__ import annotations

from experiment_engine.models import Experiment
from peacock_opportunity.models import Opportunity

from peacock_agents.models import AgentResult, AgentTask


def run_experiment_agent(experiments: list[Experiment], top_opportunities: list[Opportunity]) -> AgentResult:
    findings = [f"{e.hypothesis} ({e.status}): {e.outcome_summary or 'in progress'}" for e in experiments]
    suggested = [
        AgentTask(
            title=f"Run experiment: {opp.action}",
            detail=f"Hypothesis: {opp.action} will improve {opp.geo_opportunity}/{opp.seo_opportunity} opportunity. {opp.reason}",
            priority=opp.priority,
        )
        for opp in top_opportunities[:3]
    ]
    return AgentResult(
        agent_name="Experiment Agent",
        summary=f"{len(experiments)} logged experiment(s); suggesting {len(suggested)} new experiment(s) from top opportunities.",
        findings=findings,
        recommendations=[e.causality_caution for e in experiments[:1]]
        or ["No experiments logged yet — log one from a TOP ACTION to start building proprietary optimisation knowledge."],
        tasks=suggested,
    )
