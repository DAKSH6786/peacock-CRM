"""Final Architecture service models."""

from __future__ import annotations

from dataclasses import dataclass

from final_architecture.engine import FinalArchitectureResult, FinalArchitectureSpec


@dataclass
class FinalArchitectureCreateSpec:
    website_id: str
    name: str
    architecture: FinalArchitectureSpec
    notes: str | None = None


@dataclass
class FinalArchitectureReport:
    map_id: str
    name: str
    client_brand: str
    methodology: str
    result: FinalArchitectureResult
