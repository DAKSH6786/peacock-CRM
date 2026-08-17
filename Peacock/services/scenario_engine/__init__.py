"""Peacock Scenario Engine — counterfactual strategy ranges."""

from db_models.scenario_engine import (
    DEFAULT_METRIC,
    DEFAULT_METRIC_LABEL,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    RANGES_NOT_FAKE_PRECISION,
    STRATEGY_CODES,
    STRATEGY_LABELS,
)
from scenario_engine.models import ScenarioEngineReport, ScenarioEngineSpec
from scenario_engine.projections import (
    AssumptionInput,
    ContextSignals,
    ScenarioSpec,
    run_scenario_analysis,
)
from scenario_engine.service import ScenarioEngineService

__all__ = [
    "DEFAULT_METRIC",
    "DEFAULT_METRIC_LABEL",
    "METHODOLOGY",
    "METHODOLOGY_NOTE",
    "RANGES_NOT_FAKE_PRECISION",
    "STRATEGY_CODES",
    "STRATEGY_LABELS",
    "AssumptionInput",
    "ContextSignals",
    "ScenarioEngineReport",
    "ScenarioEngineService",
    "ScenarioEngineSpec",
    "ScenarioSpec",
    "run_scenario_analysis",
]
