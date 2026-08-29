"""SEO Agent — analyses the real SEO score + per-page technical/on-page findings."""

from __future__ import annotations

from site_intelligence.models import SiteIntelligenceReport

from peacock_agents.models import AgentDraft, AgentResult, AgentTask


def run_seo_agent(report: SiteIntelligenceReport) -> AgentResult:
    findings = [f"Site-wide SEO Score: {report.seo_score}/100."]
    recommendations: list[str] = []
    tasks: list[AgentTask] = []
    drafts: list[AgentDraft] = []
    problems: list[str] = []

    weak_pages = [p for p in report.pages if p.seo_score < 70]
    for page in weak_pages[:5]:
        problems.extend(page.whats_wrong)
        recommendations.extend(page.exact_fix[:1])
        tasks.append(
            AgentTask(
                title=f"Fix on-page SEO: {page.url}",
                detail=page.whats_wrong[0] if page.whats_wrong else "Review on-page SEO signals.",
                priority=page.priority,
            )
        )
        for fix in page.exact_fix[:1]:
            drafts.append(AgentDraft(draft_type="seo_fix", target=page.url, content=fix))

    summary = (
        f"SEO Agent reviewed {len(report.pages)} page(s); {len(weak_pages)} scored below 70/100 on the "
        "real on-page + technical SEO checklist."
    )
    return AgentResult(
        agent_name="SEO Agent",
        summary=summary,
        findings=findings,
        recommendations=recommendations or ["No SEO issues below threshold detected in this crawl."],
        tasks=tasks,
        drafts=drafts,
        problems_detected=problems,
    )
