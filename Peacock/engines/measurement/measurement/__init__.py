"""Peacock Measurement Engine, Content Decay Detector, and Competitor Change Radar.

Tracks real before/after snapshots of Peacock's own computed scores over
time. Rankings, impressions, clicks, CTR, traffic, leads, and conversions
require a real Search Console / Analytics / CRM connector and are always
reported as unavailable rather than estimated.
"""

from measurement.models import (
    DATA_UNAVAILABLE,
    EXTERNAL_METRICS,
    CompetitorChangeAlert,
    MeasurementComparison,
    MetricDelta,
    RefreshOpportunity,
    Snapshot,
)
from measurement.service import (
    capture_snapshot,
    compare_snapshots,
    detect_competitor_changes,
    detect_content_decay,
)
from measurement.store import get_history, latest

__all__ = [
    "DATA_UNAVAILABLE",
    "EXTERNAL_METRICS",
    "CompetitorChangeAlert",
    "MeasurementComparison",
    "MetricDelta",
    "RefreshOpportunity",
    "Snapshot",
    "capture_snapshot",
    "compare_snapshots",
    "detect_competitor_changes",
    "detect_content_decay",
    "get_history",
    "latest",
]
