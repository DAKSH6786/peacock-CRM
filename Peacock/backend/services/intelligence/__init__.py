"""Cognitive loop orchestrator — Layers 0–10 strategic decomposition."""

from intelligence.case import (
    CaseAgentFinding,
    CaseAssumption,
    CaseContextItem,
    CaseContradiction,
    CaseEvidence,
    CaseHypothesis,
    CaseModelUsed,
    CaseObservation,
    CaseOpportunity,
    CaseRecommendation,
    CaseRisk,
    CaseToolUsed,
    CaseUnknown,
    IntelligenceCase,
)
from intelligence.case_repository import IntelligenceCaseRepository
from intelligence.models import (
    EvidenceKind,
    PipelineResult,
    StrategicLayer,
    StrategicRequest,
    ThinkingDepth,
)
from intelligence.peacock_modes import (
    PEACOCK_MODE_PROFILES,
    ModeBudget,
    ModeBudgetTracker,
    ModeProfile,
    PeacockMode,
    list_mode_catalog,
    profile_for,
    resolve_mode,
)
from intelligence.pipeline import StrategicPipeline
from intelligence.service import IntelligenceOrchestrator

__all__ = [
    "CaseAgentFinding",
    "CaseAssumption",
    "CaseContextItem",
    "CaseContradiction",
    "CaseEvidence",
    "CaseHypothesis",
    "CaseModelUsed",
    "CaseObservation",
    "CaseOpportunity",
    "CaseRecommendation",
    "CaseRisk",
    "CaseToolUsed",
    "CaseUnknown",
    "EvidenceKind",
    "IntelligenceCase",
    "IntelligenceCaseRepository",
    "IntelligenceOrchestrator",
    "ModeBudget",
    "ModeBudgetTracker",
    "ModeProfile",
    "PEACOCK_MODE_PROFILES",
    "PeacockMode",
    "PipelineResult",
    "StrategicLayer",
    "StrategicPipeline",
    "StrategicRequest",
    "ThinkingDepth",
    "list_mode_catalog",
    "profile_for",
    "resolve_mode",
]
