"""Temporal Intelligence service models."""

from __future__ import annotations

from dataclasses import dataclass

from temporal_intelligence.analysis import TimelineAnalysisResult, TimelineSpec


@dataclass
class TemporalIntelligenceSpec:
    website_id: str
    name: str
    timeline: TimelineSpec
    notes: str | None = None


@dataclass
class TemporalIntelligenceReport:
    timeline_id: str
    name: str
    client_brand: str
    methodology: str
    result: TimelineAnalysisResult
