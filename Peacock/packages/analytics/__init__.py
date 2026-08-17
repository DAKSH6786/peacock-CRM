"""Analytics event contracts."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class AnalyticsEvent:
    organisation_id: str
    name: str
    properties: dict[str, Any] = field(default_factory=dict)
    workspace_id: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
