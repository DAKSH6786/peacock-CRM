"""Enterprise Reliability service models."""

from __future__ import annotations

from dataclasses import dataclass

from enterprise_reliability.engine import ReliabilityRunResult, ReliabilityRunSpec


@dataclass
class EnterpriseReliabilityCreateSpec:
    website_id: str
    name: str
    run: ReliabilityRunSpec
    notes: str | None = None


@dataclass
class EnterpriseReliabilityReport:
    run_id: str
    name: str
    client_brand: str
    methodology: str
    result: ReliabilityRunResult
