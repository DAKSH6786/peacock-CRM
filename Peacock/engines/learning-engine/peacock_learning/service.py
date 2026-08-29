"""Learning Engine service — in-memory ledger (process-local; see measurement.store note)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from peacock_learning.models import ConfidenceAdjustment, RecommendationRecord

_LEDGER: dict[str, RecommendationRecord] = {}

_DEFAULT_CONFIDENCE_ORDER = ["experimental", "medium", "high"]


def log_recommendation(
    *,
    recommendation: str,
    recommendation_type: str,
    page_url: str,
    baseline_score: float | None,
    confidence_at_log_time: str,
) -> RecommendationRecord:
    record = RecommendationRecord(
        record_id=str(uuid4()),
        recommendation=recommendation,
        recommendation_type=recommendation_type,
        page_url=page_url,
        logged_at=datetime.now(tz=UTC).isoformat(),
        baseline_score=baseline_score,
        confidence_at_log_time=confidence_at_log_time,
    )
    _LEDGER[record.record_id] = record
    return record


def record_result(record_id: str, *, day_bucket: int, score: float) -> RecommendationRecord:
    record = _LEDGER.get(record_id)
    if record is None:
        raise KeyError(f"Unknown recommendation record: {record_id}")
    if day_bucket == 7:
        record.result_7_day = score
    elif day_bucket == 30:
        record.result_30_day = score
    elif day_bucket == 90:
        record.result_90_day = score
    else:
        raise ValueError("day_bucket must be 7, 30, or 90")

    latest_result = record.result_90_day or record.result_30_day or record.result_7_day
    if latest_result is not None and record.baseline_score is not None:
        if latest_result > record.baseline_score + 2:
            record.outcome = "improved"
        elif latest_result < record.baseline_score - 2:
            record.outcome = "declined"
        else:
            record.outcome = "no_change"
    return record


def mark_action_taken(record_id: str) -> RecommendationRecord:
    record = _LEDGER.get(record_id)
    if record is None:
        raise KeyError(f"Unknown recommendation record: {record_id}")
    record.action_taken = True
    return record


def list_records(page_url: str | None = None, recommendation_type: str | None = None) -> list[RecommendationRecord]:
    values = list(_LEDGER.values())
    if page_url:
        values = [r for r in values if r.page_url == page_url]
    if recommendation_type:
        values = [r for r in values if r.recommendation_type == recommendation_type]
    return sorted(values, key=lambda r: r.logged_at, reverse=True)


def confidence_for_type(recommendation_type: str) -> ConfidenceAdjustment:
    """Simple historical hit-rate heuristic — never a causal claim (see CORRELATION_CAUTION)."""
    history = [
        r for r in _LEDGER.values() if r.recommendation_type == recommendation_type and r.outcome != "pending"
    ]
    if not history:
        return ConfidenceAdjustment(
            recommendation_type=recommendation_type,
            historical_sample_size=0,
            historical_hit_rate=None,
            adjusted_confidence="experimental",
        )
    hits = sum(1 for r in history if r.outcome == "improved")
    hit_rate = round(hits / len(history), 3)
    if len(history) < 3:
        adjusted = "experimental"
    elif hit_rate >= 0.7:
        adjusted = "high"
    elif hit_rate >= 0.4:
        adjusted = "medium"
    else:
        adjusted = "experimental"
    return ConfidenceAdjustment(
        recommendation_type=recommendation_type,
        historical_sample_size=len(history),
        historical_hit_rate=hit_rate,
        adjusted_confidence=adjusted,
    )
