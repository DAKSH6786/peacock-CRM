"""Research Mode service models."""

from __future__ import annotations

from dataclasses import dataclass

from research_mode.analysis import ResearchStudyResult, ResearchStudySpec


@dataclass
class ResearchModeCreateSpec:
    website_id: str
    name: str
    study: ResearchStudySpec
    notes: str | None = None


@dataclass
class ResearchModeReport:
    study_id: str
    name: str
    client_brand: str
    methodology: str
    result: ResearchStudyResult
