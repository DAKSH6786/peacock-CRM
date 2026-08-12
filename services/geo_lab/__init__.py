"""Peacock GEO Lab — controlled generative-engine experimentation."""

from db_models.geo_lab import (
    CAUSALITY_LEVELS,
    CAUSALITY_WARNING,
    GEO_LAB_METRICS,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    PAGE_ROLES,
    VARIANT_CODES,
    VARIANT_PRESETS,
)
from geo_lab.analysis import (
    ObservationSpec,
    PageSpec,
    VariantSpec,
    analyse_experiment,
    classify_causality,
    default_variants,
)
from geo_lab.models import GeoLabReport, GeoLabSpec
from geo_lab.service import GeoLabService

__all__ = [
    "CAUSALITY_LEVELS",
    "CAUSALITY_WARNING",
    "GEO_LAB_METRICS",
    "METHODOLOGY",
    "METHODOLOGY_NOTE",
    "PAGE_ROLES",
    "VARIANT_CODES",
    "VARIANT_PRESETS",
    "GeoLabReport",
    "GeoLabService",
    "GeoLabSpec",
    "ObservationSpec",
    "PageSpec",
    "VariantSpec",
    "analyse_experiment",
    "classify_causality",
    "default_variants",
]
