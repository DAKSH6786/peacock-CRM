"""Revenue Attribution service models."""

from __future__ import annotations

from dataclasses import dataclass

from revenue_attribution.attribution import AttributionAnalysisResult, AttributionSpec


@dataclass
class RevenueAttributionSpec:
    website_id: str
    name: str
    attribution: AttributionSpec
    notes: str | None = None


@dataclass
class RevenueAttributionReport:
    analysis_id: str
    name: str
    client_brand: str
    methodology: str
    result: AttributionAnalysisResult
