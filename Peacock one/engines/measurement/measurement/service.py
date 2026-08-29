"""Measurement Engine service — capture, compare, detect decay, detect competitor changes.

Never fabricates a metric it cannot measure: organic rankings, impressions,
clicks, CTR, traffic, leads, and conversions are always reported as
"Data unavailable — connector required" until a real Search Console /
Analytics / CRM connector is wired in.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from measurement.models import (
    EXTERNAL_METRICS,
    DATA_UNAVAILABLE,
    CompetitorChangeAlert,
    MeasurementComparison,
    MetricDelta,
    RefreshOpportunity,
    Snapshot,
)
from measurement.store import get_history, latest, save_snapshot

_PERIOD_DAYS = {"7_days": 7, "30_days": 30, "90_days": 90}
_DECAY_THRESHOLD = 8.0  # points drop on a 0-100 score considered a decay signal


def capture_snapshot(
    *,
    url: str,
    seo_score: float,
    aeo_score: float,
    geo_score: float,
    information_gain_score: float,
    word_count: int,
    content_hash: str | None,
    citations_count: int,
    ai_mentions: int | None = None,
    universal_share_of_answer: float | None = None,
    captured_at: datetime | None = None,
) -> Snapshot:
    snapshot = Snapshot(
        url=url,
        captured_at=captured_at or datetime.now(tz=UTC),
        seo_score=seo_score,
        aeo_score=aeo_score,
        geo_score=geo_score,
        information_gain_score=information_gain_score,
        word_count=word_count,
        content_hash=content_hash,
        citations_count=citations_count,
        ai_mentions=ai_mentions,
        universal_share_of_answer=universal_share_of_answer,
    )
    save_snapshot(snapshot)
    return snapshot


def _external_metrics_placeholder() -> dict[str, str]:
    return dict.fromkeys(EXTERNAL_METRICS, DATA_UNAVAILABLE)


def compare_snapshots(url: str, *, period: str = "30_days", custom_days: int | None = None) -> MeasurementComparison:
    history = get_history(url)
    if len(history) < 2:
        return MeasurementComparison(
            url=url,
            period_label="insufficient_history",
            baseline_captured_at=history[0].captured_at.isoformat() if history else None,
            latest_captured_at=history[-1].captured_at.isoformat() if history else None,
            deltas=[],
            external_metrics=_external_metrics_placeholder(),
            note=(
                "Only one snapshot exists for this URL — re-run the analysis again later to build "
                "before/after history. No fabricated comparison is shown."
            ),
        )

    latest_snap = history[-1]
    days = custom_days if period == "custom" and custom_days else _PERIOD_DAYS.get(period, 30)
    cutoff = latest_snap.captured_at - timedelta(days=days)
    candidates = [s for s in history[:-1] if s.captured_at <= cutoff]
    baseline = candidates[-1] if candidates else history[0]

    def delta(metric: str, base_val: float | None, latest_val: float | None) -> MetricDelta:
        if base_val is None or latest_val is None:
            return MetricDelta(metric=metric, baseline=base_val, latest=latest_val, absolute_delta=None, relative_delta_pct=None)
        abs_delta = round(latest_val - base_val, 2)
        rel = round((abs_delta / base_val) * 100.0, 2) if base_val else None
        return MetricDelta(metric=metric, baseline=base_val, latest=latest_val, absolute_delta=abs_delta, relative_delta_pct=rel)

    deltas = [
        delta("seo_score", baseline.seo_score, latest_snap.seo_score),
        delta("aeo_score", baseline.aeo_score, latest_snap.aeo_score),
        delta("geo_score", baseline.geo_score, latest_snap.geo_score),
        delta("information_gain_score", baseline.information_gain_score, latest_snap.information_gain_score),
        delta("word_count", baseline.word_count, latest_snap.word_count),
        delta("citations_count", baseline.citations_count, latest_snap.citations_count),
        delta("universal_share_of_answer", baseline.universal_share_of_answer, latest_snap.universal_share_of_answer),
    ]

    return MeasurementComparison(
        url=url,
        period_label=period if period != "custom" else f"custom_{days}_days",
        baseline_captured_at=baseline.captured_at.isoformat(),
        latest_captured_at=latest_snap.captured_at.isoformat(),
        deltas=deltas,
        external_metrics=_external_metrics_placeholder(),
        note="Peacock-computed scores compared against the closest prior snapshot at or before the requested period.",
    )


def detect_content_decay(url: str) -> RefreshOpportunity | None:
    history = get_history(url)
    if len(history) < 2:
        return None
    baseline, latest_snap = history[-2], history[-1]
    declining: list[str] = []
    if latest_snap.seo_score < baseline.seo_score - _DECAY_THRESHOLD:
        declining.append("seo_score")
    if latest_snap.aeo_score < baseline.aeo_score - _DECAY_THRESHOLD:
        declining.append("aeo_score")
    if latest_snap.geo_score < baseline.geo_score - _DECAY_THRESHOLD:
        declining.append("geo_score")
    if latest_snap.information_gain_score < baseline.information_gain_score - _DECAY_THRESHOLD:
        declining.append("information_gain_score")
    if not declining:
        return None
    return RefreshOpportunity(
        url=url,
        declining_metrics=declining,
        detail=(
            f"{', '.join(declining)} dropped by more than {_DECAY_THRESHOLD} points between "
            f"{baseline.captured_at.isoformat()} and {latest_snap.captured_at.isoformat()}."
        ),
        recommended_action="Refresh this page: update statistics, re-check entity/citation coverage, and re-run the analysis.",
        confidence="medium",
    )


def detect_competitor_changes(competitor_url: str, *, content_hash: str | None, word_count: int) -> CompetitorChangeAlert | None:
    snapshot = latest(competitor_url)
    if snapshot is None:
        return None
    if snapshot.content_hash and content_hash and snapshot.content_hash != content_hash:
        change_type = "content_updated"
        detail = f"Content hash changed since {snapshot.captured_at.isoformat()} (word count {snapshot.word_count} -> {word_count})."
    elif abs(word_count - snapshot.word_count) > max(50, int(snapshot.word_count * 0.15)):
        change_type = "content_updated"
        detail = f"Word count changed materially ({snapshot.word_count} -> {word_count}) since {snapshot.captured_at.isoformat()}."
    else:
        return None
    return CompetitorChangeAlert(
        competitor_url=competitor_url,
        change_type=change_type,
        detail=detail,
        detected_at=datetime.now(tz=UTC).isoformat(),
    )
