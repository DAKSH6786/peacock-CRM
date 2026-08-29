"""AEO Agent — direct-answer, FAQ, and answerability analysis."""

from __future__ import annotations

from site_intelligence.models import SiteIntelligenceReport

from peacock_agents.models import AgentResult, AgentTask


def run_aeo_agent(report: SiteIntelligenceReport) -> AgentResult:
    weak_pages = [p for p in report.pages if p.aeo_score < 60]
    tasks = [
        AgentTask(
            title=f"Improve answerability: {p.url}",
            detail="Add direct-answer paragraphs and FAQ schema for question-phrased headings.",
            priority=p.priority,
        )
        for p in weak_pages[:5]
    ]
    findings = [f"Site-wide AEO Score: {report.aeo_score}/100."]
    problems = [f"{p.url} has AEO score {p.aeo_score}/100 (below 60)." for p in weak_pages]

    return AgentResult(
        agent_name="AEO Agent",
        summary=f"AEO Agent found {len(weak_pages)} page(s) below a 60/100 answer-engine readiness threshold.",
        findings=findings,
        recommendations=[
            "Add FAQPage schema and question-phrased H2/H3 headings to pages with low answerability.",
            "Ensure each page opens with a direct, quotable 1-2 sentence answer.",
        ],
        tasks=tasks,
        problems_detected=problems,
    )
