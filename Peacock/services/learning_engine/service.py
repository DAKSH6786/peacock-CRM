from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class LearningEngine:
    """Architecture scaffold — business features intentionally not implemented."""

    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "learning_engine",
            "organisation_id": self.organisation_id,
            "ready": False,
            "features_implemented": False,
            "superseded_by": "learning_engine2",
            "honesty": "Legacy scaffold — use learning_engine2 for outcome recording.",
        }
