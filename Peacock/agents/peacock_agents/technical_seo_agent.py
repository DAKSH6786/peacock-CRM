"""Technical SEO Agent — robots/sitemap/status/schema/JS-rendering health."""

from __future__ import annotations

from typing import Any

from peacock_agents.models import AgentResult, AgentTask


def run_technical_seo_agent(technical_health: dict[str, Any]) -> AgentResult:
    problems: list[str] = []
    tasks: list[AgentTask] = []

    broken = technical_health.get("pages_with_broken_status", 0)
    if broken:
        problems.append(f"{broken} page(s) returned a 4xx/5xx status.")
        tasks.append(AgentTask(title="Fix broken pages", detail=f"{broken} page(s) returned an error status.", priority="Critical"))

    js_heavy = technical_health.get("pages_js_heavy", 0)
    if js_heavy:
        problems.append(f"{js_heavy} page(s) look JavaScript-heavy.")
        tasks.append(
            AgentTask(
                title="Reduce JS-render dependency",
                detail=f"{js_heavy} page(s) may be invisible to AI crawlers that do not execute JavaScript.",
                priority="High",
            )
        )

    missing_schema = technical_health.get("pages_missing_schema", 0)
    if missing_schema:
        problems.append(f"{missing_schema} page(s) have no schema.org structured data.")
        tasks.append(
            AgentTask(title="Add structured data", detail=f"{missing_schema} page(s) missing schema.org markup.", priority="Medium")
        )

    if not technical_health.get("robots_txt_present"):
        problems.append("No robots.txt was found during the crawl.")
    if not technical_health.get("sitemap_urls_found"):
        problems.append("No sitemap URLs were discovered during the crawl.")

    return AgentResult(
        agent_name="Technical SEO Agent",
        summary=f"Reviewed technical health signals from the real crawl: {len(problems)} issue(s) found.",
        findings=[f"{k}: {v}" for k, v in technical_health.items() if k != "section_scores" and k != "peacock_seo_score"],
        recommendations=[t.detail for t in tasks] or ["No technical blockers detected in this crawl."],
        tasks=tasks,
        problems_detected=problems,
    )
