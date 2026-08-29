"""Peacock Learning Engine — recommendation -> outcome ledger.

Uses historical outcomes to adjust *future confidence labels* for similar
recommendation types via a simple hit-rate heuristic. This is explicitly not
a causal claim: a recommendation being followed by an improvement does not
prove the recommendation caused it (see ``CORRELATION_CAUTION``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

CORRELATION_CAUTION = (
    "Historical outcome tracking observes correlation between a recommendation and a later score "
    "change — it does not prove causation, and is never used to guarantee a future result."
)


@dataclass(slots=True)
class RecommendationRecord:
    record_id: str
    recommendation: str
    recommendation_type: str  # title | meta | schema | citation | entity | content_gap | technical | other
    page_url: str
    logged_at: str
    baseline_score: float | None
    confidence_at_log_time: str
    action_taken: bool = False
    result_7_day: float | None = None
    result_30_day: float | None = None
    result_90_day: float | None = None
    outcome: str = "pending"  # pending | improved | no_change | declined

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ConfidenceAdjustment:
    recommendation_type: str
    historical_sample_size: int
    historical_hit_rate: float | None
    adjusted_confidence: str
    caution: str = CORRELATION_CAUTION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
