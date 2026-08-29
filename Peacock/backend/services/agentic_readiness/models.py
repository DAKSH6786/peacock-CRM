"""Agentic Web Readiness service models."""

from __future__ import annotations

from dataclasses import dataclass

from agentic_readiness.scoring import ReadinessAnalysisResult, ReadinessSpec


@dataclass
class AgenticReadinessSpec:
    website_id: str
    name: str
    readiness: ReadinessSpec
    notes: str | None = None


@dataclass
class AgenticReadinessReport:
    analysis_id: str
    name: str
    client_brand: str
    methodology: str
    result: ReadinessAnalysisResult
