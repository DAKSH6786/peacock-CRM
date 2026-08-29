"""Peacock Proprietary Metrics — documented scoring framework."""

from db_models.proprietary_metrics import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    METRIC_KEYS,
    METRIC_LABELS,
    NOT_OFFICIAL_PLATFORMS,
    PROPRIETARY_DISCLAIMER,
)
from proprietary_metrics.formulas import FORMULA_DOCS, formula_catalog
from proprietary_metrics.models import ProprietaryMetricsCreateSpec, ProprietaryMetricsReport
from proprietary_metrics.scoring import (
    MetricInputs,
    ProprietaryMetricsSpec,
    catalog,
    score_proprietary_metrics,
)
from proprietary_metrics.service import ProprietaryMetricsService

__all__ = [
    "FORMULA_DOCS",
    "METHODOLOGY",
    "METHODOLOGY_NOTE",
    "METRIC_KEYS",
    "METRIC_LABELS",
    "NOT_OFFICIAL_PLATFORMS",
    "PROPRIETARY_DISCLAIMER",
    "MetricInputs",
    "ProprietaryMetricsCreateSpec",
    "ProprietaryMetricsReport",
    "ProprietaryMetricsService",
    "ProprietaryMetricsSpec",
    "catalog",
    "formula_catalog",
    "score_proprietary_metrics",
]
