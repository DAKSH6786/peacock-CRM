"""Peacock Opportunity Engine — always-on ranked opportunities."""

from db_models.opportunity_engine import (
    ALWAYS_ON_NOTE,
    DEFAULT_RANKING_WEIGHTS,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    OPPORTUNITY_TYPES,
    RANKING_FEATURES,
)
from opportunity_engine.models import OpportunityScanReport, OpportunityScanSpec
from opportunity_engine.ranking import (
    EvidenceInput,
    OutcomeFeedbackInput,
    SignalInput,
    detect_and_rank,
    example_signals_catalog,
    learn_weights_from_outcomes,
)
from opportunity_engine.service import OpportunityEngineService

__all__ = [
    "ALWAYS_ON_NOTE",
    "DEFAULT_RANKING_WEIGHTS",
    "METHODOLOGY",
    "METHODOLOGY_NOTE",
    "OPPORTUNITY_TYPES",
    "RANKING_FEATURES",
    "EvidenceInput",
    "OpportunityEngineService",
    "OpportunityScanReport",
    "OpportunityScanSpec",
    "OutcomeFeedbackInput",
    "SignalInput",
    "detect_and_rank",
    "example_signals_catalog",
    "learn_weights_from_outcomes",
]
