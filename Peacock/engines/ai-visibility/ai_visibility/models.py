"""Peacock AI Visibility Command Center — result models.

Everything here is derived from real AI plugin responses collected through
the Peacock AI Gateway (``geo_intelligence.gateway.PeacockAIGateway``). A
plugin with no configured API key never contributes a fabricated score —
see ``available``/``reason_unavailable`` on ``EngineVisibilityReport``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

AI_VISIBILITY_DISCLAIMER = (
    "These are AI Visibility Signals / GEO Opportunities observed from real AI plugin "
    "responses to representative queries — not a guarantee of ranking, mention, or "
    "citation, and not proof that any specific keyword or phrase causes a mention."
)


@dataclass(slots=True)
class GeneratedQuery:
    intent: str  # informational | comparison | purchase | commercial
    query_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class QueryObservation:
    intent: str
    query_text: str
    engine_code: str
    engine_name: str
    simulated: bool
    brand_mentioned: bool
    recommended: bool
    recommendation_position: int | None
    competitor_mentions: list[str]
    cited_domains: list[str]
    cited_urls: list[str]
    brand_attributes: list[str]
    sentiment: str  # positive | neutral | negative | unknown

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EngineVisibilityReport:
    """One AI platform's overall visibility report (ChatGPT/Gemini/Claude/Perplexity/DeepSeek)."""

    engine_code: str
    engine_name: str
    available: bool
    reason_unavailable: str | None
    observations: list[QueryObservation] = field(default_factory=list)
    brand_mention_rate: float = 0.0  # share of answer for this engine (0-1)
    recommendation_rate: float = 0.0
    average_recommendation_position: float | None = None
    ai_share_of_voice: float | None = None  # brand mentions / (brand + competitor mentions)
    top_competitor_mentions: list[str] = field(default_factory=list)
    top_cited_domains: list[str] = field(default_factory=list)
    top_brand_attributes: list[str] = field(default_factory=list)
    dominant_sentiment: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_code": self.engine_code,
            "engine_name": self.engine_name,
            "available": self.available,
            "reason_unavailable": self.reason_unavailable,
            "observations": [o.to_dict() for o in self.observations],
            "brand_mention_rate": self.brand_mention_rate,
            "recommendation_rate": self.recommendation_rate,
            "average_recommendation_position": self.average_recommendation_position,
            "ai_share_of_voice": self.ai_share_of_voice,
            "top_competitor_mentions": list(self.top_competitor_mentions),
            "top_cited_domains": list(self.top_cited_domains),
            "top_brand_attributes": list(self.top_brand_attributes),
            "dominant_sentiment": self.dominant_sentiment,
        }


@dataclass(slots=True)
class AiVisibilityCommandCenterReport:
    brand: str
    queries: list[GeneratedQuery]
    engine_reports: list[EngineVisibilityReport]
    universal_share_of_answer: float | None  # across all available (live) engines
    universal_ai_share_of_voice: float | None
    topic_visibility: dict[str, float]
    disclaimer: str = AI_VISIBILITY_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "brand": self.brand,
            "queries": [q.to_dict() for q in self.queries],
            "engine_reports": [e.to_dict() for e in self.engine_reports],
            "universal_share_of_answer": self.universal_share_of_answer,
            "universal_ai_share_of_voice": self.universal_ai_share_of_voice,
            "topic_visibility": dict(self.topic_visibility),
            "disclaimer": self.disclaimer,
        }
