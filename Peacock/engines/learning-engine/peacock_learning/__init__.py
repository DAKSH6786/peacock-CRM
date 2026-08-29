"""Peacock Learning Engine — recommendation -> outcome tracking, confidence adjustment.

Never assumes correlation proves causation (see ``CORRELATION_CAUTION``).
"""

from peacock_learning.models import CORRELATION_CAUTION, ConfidenceAdjustment, RecommendationRecord
from peacock_learning.service import (
    confidence_for_type,
    list_records,
    log_recommendation,
    mark_action_taken,
    record_result,
)

__all__ = [
    "CORRELATION_CAUTION",
    "ConfidenceAdjustment",
    "RecommendationRecord",
    "confidence_for_type",
    "list_records",
    "log_recommendation",
    "mark_action_taken",
    "record_result",
]
