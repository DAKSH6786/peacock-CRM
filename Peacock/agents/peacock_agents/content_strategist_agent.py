"""Content Strategist Agent — turns content gaps into a prioritized content plan."""

from __future__ import annotations

from content_intelligence.models import ContentRecommendation

from peacock_agents.models import AgentDraft, AgentResult, AgentTask


def run_content_strategist_agent(recommendations: list[ContentRecommendation]) -> AgentResult:
    tasks = [
        AgentTask(
            title=f"Create {rec.content_type.replace('_', ' ')}: {rec.title}",
            detail=rec.rationale,
            priority=rec.priority,
        )
        for rec in recommendations
    ]
    drafts = [
        AgentDraft(draft_type="content_plan_item", target=rec.content_type, content=f"{rec.title} — {rec.rationale}")
        for rec in recommendations[:5]
    ]
    return AgentResult(
        agent_name="Content Strategist Agent",
        summary=f"Proposed {len(recommendations)} content item(s) across {len({r.content_type for r in recommendations})} content type(s).",
        findings=[f"{rec.content_type}: {rec.title}" for rec in recommendations],
        recommendations=[rec.rationale for rec in recommendations[:5]],
        tasks=tasks,
        drafts=drafts,
    )
