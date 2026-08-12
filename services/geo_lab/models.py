"""Peacock GEO Lab service models."""

from __future__ import annotations

from dataclasses import dataclass, field

from geo_lab.analysis import (
    CausalityAssessmentResult,
    ExperimentAnalysisResult,
    MetricDeltaResult,
    ObservationSpec,
    PageSpec,
    TimeSeriesPoint,
    VariantSpec,
)


@dataclass
class GeoLabSpec:
    website_id: str
    name: str
    client_brand: str
    hypothesis: str
    variants: list[VariantSpec]
    pages: list[PageSpec]
    observations: list[ObservationSpec]
    topic_cluster: str | None = None
    design_type: str = "before_after_with_controls"
    pre_window_start: str | None = None
    pre_window_end: str | None = None
    post_window_start: str | None = None
    post_window_end: str | None = None
    intervention_date: str | None = None
    known_confounds: list[str] = field(default_factory=list)
    concurrent_changes: list[str] = field(default_factory=list)
    notes: str | None = None
    use_default_variants_if_empty: bool = True


@dataclass
class GeoLabReport:
    experiment_id: str
    name: str
    client_brand: str
    hypothesis: str
    methodology: str
    design_type: str
    design_features: list[str]
    causality_warning: str
    overall_causality_level: str
    overall_summary: str
    variants: list[dict]
    pages: list[dict]
    deltas: list[MetricDeltaResult]
    causality_assessments: list[CausalityAssessmentResult]
    time_series: list[TimeSeriesPoint]
    auto_causal_conclusion_rejected: bool = True
    analysis: ExperimentAnalysisResult | None = None
