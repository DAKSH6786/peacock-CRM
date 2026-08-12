from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class WriterEngine:
    """Legacy scaffold — prefer WriterIntelligenceService for outcome decisions."""

    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "writer_engine",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": False,
            "superseded_by": "writer_intelligence",
            "note": (
                "Use services.writer_intelligence for Writer DNA, "
                "Writer×Topic×Client outcome prediction, and the Writer Outcome Graph. "
                "Do not use sample-embedding similarity as the primary recommender."
            ),
        }
