"""Writer Intelligence 2.0 service models."""

from __future__ import annotations

from dataclasses import dataclass, field

from writer_intelligence.scoring import (
    ArticleOutcomeHistory,
    DecisionContext,
    IntelligenceResult,
    WriterCandidate,
)


@dataclass
class WriterIntelligenceSpec:
    website_id: str
    name: str
    context: DecisionContext
    writers: list[WriterCandidate]
    history: list[ArticleOutcomeHistory] = field(default_factory=list)
    notes: str | None = None


@dataclass
class WriterIntelligenceReport:
    analysis_id: str
    name: str
    client_brand: str
    industry: str
    topic: str
    audience: str
    methodology: str
    result: IntelligenceResult
