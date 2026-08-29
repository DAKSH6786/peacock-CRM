"""Peacock AI Agents — shared result contract.

Every agent analyses real data already computed by Peacock's engines (a
``SiteIntelligenceReport``, a citation/measurement/experiment result, etc.)
and returns findings, recommendations, tasks, and optional drafts. Agents are
read-only analysts and draft-preparers by construction: none of them call a
publishing connector, delete anything, or modify production systems. Any
action that would do so requires an explicit human approval step (see
``experts`` and ``publishing``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

AGENT_GUARDRAIL_NOTE = (
    "This agent only analyses, recommends, and drafts — it cannot publish, delete, or modify "
    "production systems. Those actions always require explicit human approval."
)


@dataclass(slots=True)
class AgentTask:
    title: str
    detail: str
    priority: str  # Critical | High | Medium | Low
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentDraft:
    draft_type: str  # e.g. title, meta_description, faq, content_brief, schema
    target: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AgentResult:
    agent_name: str
    summary: str
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    tasks: list[AgentTask] = field(default_factory=list)
    drafts: list[AgentDraft] = field(default_factory=list)
    problems_detected: list[str] = field(default_factory=list)
    guardrail_note: str = AGENT_GUARDRAIL_NOTE

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "summary": self.summary,
            "findings": list(self.findings),
            "recommendations": list(self.recommendations),
            "tasks": [t.to_dict() for t in self.tasks],
            "drafts": [d.to_dict() for d in self.drafts],
            "problems_detected": list(self.problems_detected),
            "guardrail_note": self.guardrail_note,
        }
