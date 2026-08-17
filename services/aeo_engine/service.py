from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class AeoEngine:
    """Architecture scaffold — business features intentionally not implemented."""

    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "aeo_engine",
            "organisation_id": self.organisation_id,
            "ready": False,
            "features_implemented": False,
            "honesty": "Scaffold only — AEO business features are not implemented.",
        }
