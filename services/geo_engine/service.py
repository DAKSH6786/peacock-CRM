"""GEO engine — Probabilistic AI Visibility (controlled multi-run measurement)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from geo_engine.probabilistic_models import (
    DEFAULT_REPETITIONS,
    HARD_MAX_REPETITIONS,
    CampaignSpec,
    ProbeCellSpec,
    RateLimitPolicy,
    VisibilityScoreCardView,
)
from geo_engine.probabilistic_service import ProbabilisticVisibilityService


@dataclass(slots=True)
class GeoEngine:
    """Generative visibility engine with probabilistic measurement support."""

    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "geo_engine",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": True,
            "probabilistic_ai_visibility": True,
            "single_shot_rejected": True,
            "defaults": {
                "target_repetitions": DEFAULT_REPETITIONS,
                "hard_max_repetitions": HARD_MAX_REPETITIONS,
            },
            "guarantees": [
                "controlled_repetitions",
                "rate_limited_traffic",
                "distributional_metrics",
                "peacock_visibility_confidence",
            ],
        }

    def visibility_service(self, session: Session) -> ProbabilisticVisibilityService:
        return ProbabilisticVisibilityService(session)


__all__ = [
    "CampaignSpec",
    "GeoEngine",
    "ProbeCellSpec",
    "ProbabilisticVisibilityService",
    "RateLimitPolicy",
    "VisibilityScoreCardView",
]
