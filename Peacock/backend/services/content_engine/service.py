from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ContentEngine:
    """Legacy scaffold — prefer ContentLabService for multi-opportunity evaluation."""

    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "content_engine",
            "organisation_id": self.organisation_id,
            "ready": False,
            "features_implemented": False,
            "superseded_by": "content_lab + content_digital_twin",
            "note": (
                "Use services.content_lab for Information Gain, Content Moat, "
                "and Generative Citability (proprietary estimate). "
                "Use services.content_digital_twin to simulate article plans "
                "before publish and rerun after plan edits."
            ),
        }
