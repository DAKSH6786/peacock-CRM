"""Peacock Scenario Engine service models."""

from __future__ import annotations

from dataclasses import dataclass

from scenario_engine.projections import ScenarioAnalysisResult, ScenarioSpec


@dataclass
class ScenarioEngineSpec:
    website_id: str
    name: str
    scenario: ScenarioSpec
    notes: str | None = None


@dataclass
class ScenarioEngineReport:
    analysis_id: str
    name: str
    client_brand: str
    methodology: str
    result: ScenarioAnalysisResult
