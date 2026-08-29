"""Typed results for the Peacock GEO Intelligence Layer.

Architecture: AI Plugins -> Peacock AI Gateway -> Multi-LLM Response Collection
-> Peacock GEO Intelligence Layer -> Keyword/Entity/Citation Extraction ->
Platform-Specific GEO Recommendations -> Peacock One Dashboard.

Nothing here is provider-specific — these models describe the *output* of
whichever LLM plugins were broadcast to, never the plugins themselves.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

GEO_DISCLAIMER = (
    "These are GEO opportunities / AI visibility signals derived from observed LLM "
    "responses — not a guarantee of ranking, mention, or citation on any platform."
)

METHODOLOGY_NOTE = (
    "Peacock GEO Intelligence sends the same research prompt to every enabled AI plugin "
    "through the Peacock AI Gateway, then deterministically extracts keywords, entities, "
    "questions, citations, competitor mentions, and per-platform terminology from the "
    "collected responses. Recommendations are platform-specific signals, not guarantees."
)


@dataclass(slots=True)
class ProviderResponse:
    """One AI plugin's answer to the same broadcast research prompt."""

    engine_code: str
    engine_name: str
    provider_code: str
    content: str
    simulated: bool
    model: str | None = None
    latency_ms: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class KeywordSignal:
    phrase: str
    frequency: int
    engine_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EntityMention:
    name: str
    kind: str  # "client" | "competitor" | "other"
    frequency: int
    engine_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QuestionSignal:
    question: str
    engine_code: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CitationSignal:
    url: str
    domain: str
    source_class: str
    engine_code: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TerminologyProfile:
    """How a given LLM tends to phrase things — its distinct terminology."""

    engine_code: str
    engine_name: str
    top_terms: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TopicSignal:
    topic: str
    associated_entity: str | None
    frequency: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GeoExtractionResult:
    keywords: list[KeywordSignal]
    entities: list[EntityMention]
    questions: list[QuestionSignal]
    citations: list[CitationSignal]
    competitor_mentions: list[EntityMention]
    terminology_by_engine: list[TerminologyProfile]
    top_brand_topics: list[TopicSignal]
    missing_topics: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "keywords": [k.to_dict() for k in self.keywords],
            "entities": [e.to_dict() for e in self.entities],
            "questions": [q.to_dict() for q in self.questions],
            "citations": [c.to_dict() for c in self.citations],
            "competitor_mentions": [c.to_dict() for c in self.competitor_mentions],
            "terminology_by_engine": [t.to_dict() for t in self.terminology_by_engine],
            "top_brand_topics": [t.to_dict() for t in self.top_brand_topics],
            "missing_topics": list(self.missing_topics),
        }


@dataclass(slots=True)
class PlatformRecommendation:
    """GEO opportunities for one platform — never a guaranteed-ranking claim."""

    engine_code: str
    engine_name: str
    platform_label: str
    opportunities: list[str]
    signal_strength: str  # "low" | "medium" | "high"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class GeoIntelligenceReport:
    client_brand: str
    research_prompt: str
    competitors: list[str]
    site_topics: list[str]
    provider_responses: list[ProviderResponse]
    extraction: GeoExtractionResult
    recommendations: list[PlatformRecommendation]
    disclaimer: str = GEO_DISCLAIMER
    methodology_note: str = METHODOLOGY_NOTE

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "research_prompt": self.research_prompt,
            "competitors": list(self.competitors),
            "site_topics": list(self.site_topics),
            "provider_responses": [r.to_dict() for r in self.provider_responses],
            **self.extraction.to_dict(),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "disclaimer": self.disclaimer,
            "methodology_note": self.methodology_note,
        }
