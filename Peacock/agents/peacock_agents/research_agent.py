"""Research Agent — summarises the AI Visibility Command Center scan."""

from __future__ import annotations

from ai_visibility.models import AiVisibilityCommandCenterReport

from peacock_agents.models import AgentResult, AgentTask


def run_research_agent(report: AiVisibilityCommandCenterReport) -> AgentResult:
    live = [e for e in report.engine_reports if e.available]
    unavailable = [e for e in report.engine_reports if not e.available]

    findings = [
        f"Universal share of answer across live plugins: {report.universal_share_of_answer if report.universal_share_of_answer is not None else 'Data unavailable — no live AI plugin configured'}."
    ]
    for e in live:
        findings.append(
            f"{e.engine_name}: mention rate {e.brand_mention_rate:.0%}, recommendation rate {e.recommendation_rate:.0%}, "
            f"share of voice {e.ai_share_of_voice if e.ai_share_of_voice is not None else 'n/a'}."
        )

    tasks = [
        AgentTask(
            title=f"Investigate low AI visibility on {e.engine_name}",
            detail=f"Mention rate {e.brand_mention_rate:.0%} across {len(e.observations)} representative quer(y/ies).",
            priority="High" if e.brand_mention_rate < 0.3 else "Medium",
        )
        for e in live
        if e.brand_mention_rate < 0.5
    ]

    return AgentResult(
        agent_name="Research Agent",
        summary=(
            f"Ran {len(report.queries)} representative queries across {len(report.engine_reports)} AI plugin(s); "
            f"{len(live)} live, {len(unavailable)} require an API key."
        ),
        findings=findings,
        recommendations=[
            "Cover the topics and questions used in this scan directly on-site to improve future mention likelihood."
        ],
        tasks=tasks,
        problems_detected=[f"{e.engine_name}: {e.reason_unavailable}" for e in unavailable],
    )
