"""Content Strategy Engine + Content Creation Studio — result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class ContentGraphNode:
    kind: str  # brand | topic | subtopic | entity | keyword | query | prompt | page
    key: str
    label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ContentGraphEdge:
    from_kind: str
    from_key: str
    to_kind: str
    to_key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ContentGraph:
    nodes: list[ContentGraphNode] = field(default_factory=list)
    edges: list[ContentGraphEdge] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": [n.to_dict() for n in self.nodes], "edges": [e.to_dict() for e in self.edges]}


@dataclass(slots=True)
class ContentRecommendation:
    content_type: str  # pillar_page | topic_cluster | supporting_article | comparison_page | ...
    title: str
    rationale: str
    target_topics: list[str]
    priority: str  # Critical | High | Medium | Low

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ContentBrief:
    """CREATE WITH PEACOCK — a drafting brief. Never fabricates facts; every
    placeholder that would require an external fact is marked for human input."""

    topic: str
    research_notes: list[str]
    outline: list[str]
    draft_skeleton: str
    sources_needed: list[str]
    faqs: list[dict[str, str]]
    suggested_title: str
    suggested_meta_description: str
    suggested_schema: str
    internal_link_suggestions: list[str]
    cta_suggestion: str
    optimization_checklist: list[str]
    confidence: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
