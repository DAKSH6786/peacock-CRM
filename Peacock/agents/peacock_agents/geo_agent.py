"""GEO Agent — Generative Engine Optimisation analysis using the 7-factor GEO Score."""

from __future__ import annotations

from site_intelligence.models import SiteIntelligenceReport

from peacock_agents.models import AgentResult, AgentTask


def run_geo_agent(report: SiteIntelligenceReport) -> AgentResult:
    gb = report.geo_score_breakdown
    factors = [
        gb.entity_authority,
        gb.citation_readiness,
        gb.answerability,
        gb.evidence,
        gb.topical_coverage,
        gb.technical_ai_accessibility,
        gb.brand_authority,
    ]
    weak = [f for f in factors if f.score < 50]
    tasks = [
        AgentTask(
            title=f"Improve {f.label}",
            detail=f.summary,
            priority="High" if f.score < 30 else "Medium",
        )
        for f in weak
    ]
    return AgentResult(
        agent_name="GEO Agent",
        summary=f"Site-wide GEO Score {report.geo_score}/100. Formula: {gb.formula}",
        findings=[f"{f.label}: {f.score}/100 — {f.summary}" for f in factors],
        recommendations=[f"Strengthen {f.label.lower()}: {f.summary}" for f in weak]
        or ["All 7 GEO factors are at or above 50/100 for the representative page analysed."],
        tasks=tasks,
        problems_detected=[f"{f.label} scored {f.score}/100 (below 50)." for f in weak],
    )
