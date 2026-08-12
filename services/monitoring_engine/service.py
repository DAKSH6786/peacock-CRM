from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MonitoringEngine:
    """Architecture scaffold — business features intentionally not implemented."""

    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "monitoring_engine",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": False,
        }
