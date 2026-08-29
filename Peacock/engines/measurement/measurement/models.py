"""Measurement Engine, Content Decay Detector, Competitor Change Radar — models.

Every number here comes from Peacock's own re-crawl/re-score of a page over
time (a real, stored snapshot) or is explicitly marked unavailable. Rankings,
impressions, clicks, CTR, traffic, leads, and conversions require a real
Search Console / Analytics / CRM connector that is not configured in this
deployment — they are never estimated or fabricated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

DATA_UNAVAILABLE = "Data unavailable — connector required"

EXTERNAL_METRICS = (
    "organic_rankings",
    "impressions",
    "clicks",
    "ctr",
    "traffic",
    "leads",
    "conversions",
)


@dataclass(slots=True)
class Snapshot:
    url: str
    captured_at: datetime
    seo_score: float
    aeo_score: float
    geo_score: float
    information_gain_score: float
    word_count: int
    content_hash: str | None
    citations_count: int
    ai_mentions: int | None  # None when no live AI plugin measured this run
    universal_share_of_answer: float | None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["captured_at"] = self.captured_at.isoformat()
        return d


@dataclass(slots=True)
class MetricDelta:
    metric: str
    baseline: float | None
    latest: float | None
    absolute_delta: float | None
    relative_delta_pct: float | None


@dataclass(slots=True)
class MeasurementComparison:
    url: str
    period_label: str  # "7_days" | "30_days" | "90_days" | "custom" | "insufficient_history"
    baseline_captured_at: str | None
    latest_captured_at: str | None
    deltas: list[MetricDelta] = field(default_factory=list)
    external_metrics: dict[str, str] = field(default_factory=lambda: dict.fromkeys(EXTERNAL_METRICS, DATA_UNAVAILABLE))
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "period_label": self.period_label,
            "baseline_captured_at": self.baseline_captured_at,
            "latest_captured_at": self.latest_captured_at,
            "deltas": [asdict(d) for d in self.deltas],
            "external_metrics": dict(self.external_metrics),
            "note": self.note,
        }


@dataclass(slots=True)
class RefreshOpportunity:
    url: str
    declining_metrics: list[str]
    detail: str
    recommended_action: str
    confidence: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CompetitorChangeAlert:
    competitor_url: str
    change_type: str  # new_page | content_updated | new_citation_signal | none
    detail: str
    detected_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
