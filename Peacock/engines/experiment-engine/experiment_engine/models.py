"""Peacock Experiment Engine — structured SEO/GEO experiments.

Stores hypothesis/page/change/baseline/comparison records. Outcomes are
computed from real re-analysis snapshots (via the Measurement Engine) —
Peacock never assumes correlation proves causation, and always labels the
result with the same causality caution used by the GEO Lab.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

CAUSALITY_CAUTION = (
    "An observed change after this experiment does not by itself prove the change caused it — "
    "seasonality, algorithm updates, and other concurrent changes may also explain a shift."
)

EXPERIMENT_STATUSES = ("running", "completed", "inconclusive")


@dataclass(slots=True)
class Experiment:
    experiment_id: str
    hypothesis: str
    page_url: str
    change_description: str
    change_category: str  # answer_blocks | entities | citations | internal_links | statistics | schema | restructuring | other
    baseline_snapshot_at: str | None
    start_date: str
    status: str = "running"
    comparison_snapshot_at: str | None = None
    outcome_summary: str | None = None
    confidence: str = "experimental"
    causality_caution: str = CAUSALITY_CAUTION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExperimentStore:
    experiments: dict[str, Experiment] = field(default_factory=dict)
