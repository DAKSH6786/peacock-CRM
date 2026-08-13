"""Proprietary Metrics service models."""

from __future__ import annotations

from dataclasses import dataclass

from proprietary_metrics.scoring import ProprietaryMetricsResult, ProprietaryMetricsSpec


@dataclass
class ProprietaryMetricsCreateSpec:
    website_id: str
    name: str
    scorecard: ProprietaryMetricsSpec
    notes: str | None = None


@dataclass
class ProprietaryMetricsReport:
    scorecard_id: str
    name: str
    client_brand: str
    methodology: str
    result: ProprietaryMetricsResult
