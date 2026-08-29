"""Cost Intelligence service models."""

from __future__ import annotations

from dataclasses import dataclass

from cost_intelligence.budget_engine import BudgetEstimateResult, BudgetEstimateSpec


@dataclass
class CostIntelligenceCreateSpec:
    website_id: str
    name: str
    estimate: BudgetEstimateSpec
    notes: str | None = None


@dataclass
class CostIntelligenceReport:
    estimate_id: str
    name: str
    client_brand: str
    methodology: str
    result: BudgetEstimateResult
