"""Quality Bar service models."""

from __future__ import annotations

from dataclasses import dataclass

from quality_bar.engine import QualityBarResult, QualityBarSpec


@dataclass
class QualityBarCreateSpec:
    website_id: str
    name: str
    assessment: QualityBarSpec
    notes: str | None = None


@dataclass
class QualityBarReport:
    assessment_id: str
    name: str
    client_brand: str
    methodology: str
    result: QualityBarResult
