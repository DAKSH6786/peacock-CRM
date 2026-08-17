from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CompetitorEngine:
    """Legacy scaffold — prefer DeepCompetitorService for multi-category intelligence."""

    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "competitor_engine",
            "organisation_id": self.organisation_id,
            "ready": False,
            "features_implemented": False,
            "superseded_by": "deep_competitor",
            "note": (
                "Use services.deep_competitor for automatic multi-category discovery, "
                "Competitive Delta Engine, and differentiated (no-copy) strategies."
            ),
        }
