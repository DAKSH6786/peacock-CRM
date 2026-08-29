"""Peacock Opportunity Engine — prioritized action list, not a wall of warnings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class Opportunity:
    action: str
    reason: str
    affected_page: str
    seo_opportunity: str  # Critical | High | Medium | Low
    aeo_opportunity: str
    geo_opportunity: str
    ai_visibility_opportunity: str
    business_value: str
    competitor_gap: str
    implementation_difficulty: str  # Low | Medium | High
    confidence: str  # high | medium | experimental
    priority: str  # Critical | High | Medium | Low
    peacock_impact_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
