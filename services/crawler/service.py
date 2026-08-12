from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CrawlerService:
    """Architecture scaffold — business features intentionally not implemented."""

    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "crawler",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": False,
            "adapters": ["httpx", "beautifulsoup", "playwright(stub)"],
        }
