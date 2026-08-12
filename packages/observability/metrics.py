from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(slots=True)
class CostRecord:
    provider: str
    model: str
    organisation_id: str
    operation: str
    usage: TokenUsage
    cost_usd_micros: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


class UsageTracker:
    """In-memory tracker used by adapters; persist via audit/usage repositories."""

    def __init__(self) -> None:
        self._records: list[CostRecord] = []

    def record(self, record: CostRecord) -> None:
        self._records.append(record)

    def records_for_org(self, organisation_id: str) -> list[CostRecord]:
        return [r for r in self._records if r.organisation_id == organisation_id]

    def total_cost_usd_micros(self, organisation_id: str) -> int:
        return sum(r.cost_usd_micros for r in self.records_for_org(organisation_id))

    def clear(self) -> None:
        self._records.clear()
