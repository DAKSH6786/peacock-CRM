"""Executive Brain service models."""

from __future__ import annotations

from dataclasses import dataclass

from executive_brain.synthesis import ExecutiveBrainResult, ExecutiveBrainSpec


@dataclass
class ExecutiveBrainCreateSpec:
    website_id: str
    name: str
    brief: ExecutiveBrainSpec
    notes: str | None = None


@dataclass
class ExecutiveBrainReport:
    brief_id: str
    name: str
    client_brand: str
    methodology: str
    result: ExecutiveBrainResult
