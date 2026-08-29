"""Peacock Growth Loop — the flagship end-to-end workflow.

    SEO + AEO + GEO -> AI Visibility -> LLM Intelligence -> Opportunity
    Discovery -> Content Strategy -> Content Creation -> Optimization ->
    AI Agents -> Human Experts -> Publishing -> Measurement -> Experiments
    -> Learning -> Re-optimization

Every stage below is populated from a REAL computation (a crawl, a live/
simulated AI plugin broadcast, or a deterministic scoring formula already
used elsewhere in Peacock One) — nothing here is a placeholder value
pretending to be a measurement. See each stage's own ``disclaimer``/
``data_availability`` fields for exactly what is/isn't measured.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class GrowthLoopStage:
    stage: str
    status: str  # completed | skipped | unavailable
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GrowthLoopReport:
    url: str
    brand: str
    stages: list[GrowthLoopStage]

    site_intelligence: dict[str, Any]
    ai_visibility: dict[str, Any]
    citation_gaps: dict[str, Any]
    content_recommendations: list[dict[str, Any]]
    content_graph: dict[str, Any]
    top_content_brief: dict[str, Any] | None
    content_simulation: dict[str, Any] | None
    top_opportunities: list[dict[str, Any]]
    agent_results: dict[str, Any]
    expert_task: dict[str, Any] | None
    publishing_preview: dict[str, Any] | None
    measurement_snapshot: dict[str, Any] | None
    learning_record: dict[str, Any] | None
    executive_summary: dict[str, Any]
    disclaimer: str = (
        "The Peacock Growth Loop chains real crawl, scoring, and (where configured) live AI-plugin "
        "signals end to end. GEO/AI-visibility results are opportunities and readiness estimates, not "
        "guarantees of ranking, mention, or citation. Nothing is published, deleted, or changed in "
        "production without explicit human approval."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "brand": self.brand,
            "stages": [s.to_dict() for s in self.stages],
            "site_intelligence": self.site_intelligence,
            "ai_visibility": self.ai_visibility,
            "citation_gaps": self.citation_gaps,
            "content_recommendations": self.content_recommendations,
            "content_graph": self.content_graph,
            "top_content_brief": self.top_content_brief,
            "content_simulation": self.content_simulation,
            "top_opportunities": self.top_opportunities,
            "agent_results": self.agent_results,
            "expert_task": self.expert_task,
            "publishing_preview": self.publishing_preview,
            "measurement_snapshot": self.measurement_snapshot,
            "learning_record": self.learning_record,
            "executive_summary": self.executive_summary,
            "disclaimer": self.disclaimer,
        }
