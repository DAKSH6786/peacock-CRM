"""Anomaly Engine — detect unusual shifts and rank by probable business impact."""

from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from db_models.anomaly_engine import (
    ANOMALY_LABELS,
    ANOMALY_TYPES,
    IMPACT_PRIORS,
    METHODOLOGY_NOTE,
    SEVERITY_LEVELS,
)


MIN_POINTS = 6
Z_ALERT = 2.4
MIN_REL_CHANGE = 0.12


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


@dataclass
class MetricObservation:
    metric_key: str
    anomaly_type: str
    points: list[tuple[datetime, float]]  # (ts, value)
    # Optional: estimated revenue tied to this metric surface
    revenue_exposure: float | None = None
    label_hint: str | None = None

    def validate(self) -> None:
        if self.anomaly_type not in ANOMALY_TYPES:
            raise ValueError(f"Unsupported anomaly_type: {self.anomaly_type}")
        if len(self.points) < 2:
            raise ValueError("points require at least 2 values")


@dataclass
class AnomalyScanSpec:
    client_brand: str
    window_start: datetime
    window_end: datetime
    observations: list[MetricObservation] = field(default_factory=list)
    # Global revenue exposure fallback for ranking when per-metric missing
    default_revenue_exposure: float = 0.0


@dataclass(slots=True)
class AnomalyResult:
    anomaly_type: str
    anomaly_label: str
    title: str
    detail: str
    detected_at: datetime
    severity: str
    magnitude: float
    z_score: float
    impact_score: float
    impact_rank: int
    revenue_exposure: float | None
    metric_key: str | None
    baseline_value: float | None
    current_value: float | None
    recommended_response: str
    is_noise: bool

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["detected_at"] = self.detected_at.isoformat()
        return d


@dataclass
class AnomalyScanResult:
    window_start: datetime
    window_end: datetime
    anomalies: list[AnomalyResult]
    anomalies_detected: int
    critical_count: int
    high_count: int
    top_anomaly_type: str | None
    top_impact_score: float | None
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "anomalies": [a.to_dict() for a in self.anomalies],
            "anomalies_detected": self.anomalies_detected,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "top_anomaly_type": self.top_anomaly_type,
            "top_impact_score": self.top_impact_score,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
        }


def _severity(z: float, rel: float) -> str:
    if z >= 4.0 or rel >= 0.45:
        return "critical"
    if z >= 3.2 or rel >= 0.30:
        return "high"
    if z >= Z_ALERT or rel >= MIN_REL_CHANGE:
        return "medium"
    return "low"


def _response(anomaly_type: str) -> str:
    return {
        "sudden_ranking_loss": (
            "Audit ranking drops by query cluster; check cannibalisation, "
            "technical regressions, and competitor SERP shifts."
        ),
        "ai_visibility_collapse": (
            "Compare AI answer presence before/after; refresh entity clarity "
            "and answer-ready sections for affected prompts."
        ),
        "citation_disappearance": (
            "Inspect lost citing sources and content provenance; restore "
            "citable claims and third-party corroboration."
        ),
        "negative_sentiment_spike": (
            "Review answer/snippet sentiment drivers; address inaccurate or "
            "hostile narratives in source content."
        ),
        "competitor_acceleration": (
            "Map competitor content/authority moves; prioritise differentiated "
            "counter-plays where impact is highest."
        ),
        "crawler_issue": (
            "Check robots, crawl budget, server errors, and blocked resources; "
            "validate Googlebot/AI crawler access."
        ),
        "indexation_loss": (
            "Verify canonical/noindex/coverage issues; request recrawl for "
            "critical URLs after fixes."
        ),
        "traffic_anomaly": (
            "Segment traffic loss by landing page and channel; correlate with "
            "ranking, indexation, and seasonal baselines."
        ),
        "backlink_loss": (
            "Identify lost referring domains; assess toxicity vs valuable links "
            "and pursue recovery or replacements."
        ),
    }.get(anomaly_type, "Investigate metric shift and contain business exposure.")


def _impact_score(
    anomaly_type: str,
    severity: str,
    z: float,
    rel: float,
    revenue_exposure: float | None,
) -> float:
    prior = IMPACT_PRIORS.get(anomaly_type, 0.5)
    sev_w = {"low": 0.35, "medium": 0.55, "high": 0.75, "critical": 0.95}[severity]
    signal = min(1.0, (z / 5.0) * 0.5 + min(rel, 1.0) * 0.5)
    rev = 0.0
    if revenue_exposure and revenue_exposure > 0:
        # log-scaled exposure contribution
        rev = min(1.0, math.log10(revenue_exposure + 1) / 6.0)
    score = 100.0 * (0.45 * prior + 0.30 * sev_w + 0.15 * signal + 0.10 * rev)
    return round(_clamp100(score), 1)


def detect_on_series(obs: MetricObservation) -> AnomalyResult | None:
    """Detect a single anomaly from a metric series (baseline vs recent)."""
    obs.validate()
    pts = sorted(obs.points, key=lambda p: p[0])
    if len(pts) < MIN_POINTS:
        return None
    split = max(MIN_POINTS - 2, len(pts) - 3)
    baseline = [v for _, v in pts[:split]]
    recent = [v for _, v in pts[split:]]
    if not baseline or not recent:
        return None
    b_mean = statistics.fmean(baseline)
    b_std = statistics.pstdev(baseline) if len(baseline) > 1 else 0.0
    b_std = b_std or 1e-6
    r_mean = statistics.fmean(recent)
    delta = r_mean - b_mean
    # For most loss anomalies, negative delta is the signal; competitor_acceleration
    # and negative_sentiment_spike may be positive (bad) depending on metric encoding.
    z = abs(delta) / b_std
    rel = abs(delta) / max(abs(b_mean), 1e-6)

    # Direction expectations
    loss_types = {
        "sudden_ranking_loss",
        "ai_visibility_collapse",
        "citation_disappearance",
        "indexation_loss",
        "traffic_anomaly",
        "backlink_loss",
        "crawler_issue",
    }
    spike_types = {"negative_sentiment_spike", "competitor_acceleration"}
    if obs.anomaly_type in loss_types and delta >= 0:
        # Improvement or flat — not an anomaly for loss types
        if z < Z_ALERT:
            return None
        # Large positive swing still flagged only if explicitly traffic_anomaly upside?
        if obs.anomaly_type != "traffic_anomaly":
            return None
    if obs.anomaly_type in spike_types and delta <= 0 and z < Z_ALERT:
        return None

    if z < Z_ALERT and rel < MIN_REL_CHANGE:
        return None

    severity = _severity(z, rel)
    detected_at = pts[split][0]
    magnitude = round(abs(delta), 3)
    exposure = obs.revenue_exposure
    impact = _impact_score(obs.anomaly_type, severity, z, rel, exposure)
    title = obs.label_hint or f"{ANOMALY_LABELS[obs.anomaly_type]} on {obs.metric_key}"
    detail = (
        f"{ANOMALY_LABELS[obs.anomaly_type]}: baseline {b_mean:.2f} → recent {r_mean:.2f} "
        f"(Δ={delta:+.2f}, z={z:.2f}, rel={rel:.0%})."
    )
    return AnomalyResult(
        anomaly_type=obs.anomaly_type,
        anomaly_label=ANOMALY_LABELS[obs.anomaly_type],
        title=title,
        detail=detail,
        detected_at=detected_at,
        severity=severity,
        magnitude=magnitude,
        z_score=round(z, 3),
        impact_score=impact,
        impact_rank=0,
        revenue_exposure=exposure,
        metric_key=obs.metric_key,
        baseline_value=round(b_mean, 3),
        current_value=round(r_mean, 3),
        recommended_response=_response(obs.anomaly_type),
        is_noise=False,
    )


def demo_observations(window_end: datetime | None = None) -> list[MetricObservation]:
    """Deterministic demo series covering all anomaly types."""
    end = window_end or datetime.now(UTC)
    start = end - timedelta(days=20)

    def series(vals: list[float]) -> list[tuple[datetime, float]]:
        return [(start + timedelta(days=i), v) for i, v in enumerate(vals)]

    # 14 baseline-ish + drop/spike in last points
    return [
        MetricObservation(
            "organic_rank_score",
            "sudden_ranking_loss",
            series([70, 71, 69, 70, 72, 71, 70, 69, 71, 70, 68, 55, 50, 48]),
            revenue_exposure=250_000,
            label_hint="Sudden ranking loss on core queries",
        ),
        MetricObservation(
            "ai_visibility_score",
            "ai_visibility_collapse",
            series([40, 41, 39, 40, 42, 41, 40, 39, 40, 38, 25, 18, 15, 14]),
            revenue_exposure=180_000,
            label_hint="AI visibility collapse",
        ),
        MetricObservation(
            "citation_count",
            "citation_disappearance",
            series([20, 21, 19, 20, 22, 21, 20, 19, 20, 18, 8, 5, 4, 3]),
            revenue_exposure=120_000,
        ),
        MetricObservation(
            "negative_sentiment_rate",
            "negative_sentiment_spike",
            series([0.1, 0.12, 0.11, 0.1, 0.09, 0.11, 0.1, 0.12, 0.11, 0.15, 0.28, 0.35, 0.4, 0.42]),
            revenue_exposure=60_000,
        ),
        MetricObservation(
            "competitor_visibility",
            "competitor_acceleration",
            series([30, 31, 29, 30, 32, 31, 30, 29, 31, 33, 45, 52, 55, 58]),
            revenue_exposure=90_000,
        ),
        MetricObservation(
            "crawl_success_rate",
            "crawler_issue",
            series([0.98, 0.97, 0.99, 0.98, 0.97, 0.98, 0.99, 0.98, 0.97, 0.95, 0.7, 0.55, 0.5, 0.48]),
            revenue_exposure=40_000,
        ),
        MetricObservation(
            "indexed_pages",
            "indexation_loss",
            series([1200, 1195, 1205, 1210, 1200, 1198, 1202, 1200, 1190, 1100, 900, 820, 800, 790]),
            revenue_exposure=150_000,
        ),
        MetricObservation(
            "organic_sessions",
            "traffic_anomaly",
            series([5000, 5100, 4950, 5050, 5200, 5100, 5000, 4900, 5050, 4800, 3200, 2800, 2600, 2500]),
            revenue_exposure=300_000,
        ),
        MetricObservation(
            "referring_domains",
            "backlink_loss",
            series([400, 402, 398, 401, 405, 400, 399, 402, 400, 390, 340, 310, 300, 295]),
            revenue_exposure=80_000,
        ),
    ]


def scan_anomalies(spec: AnomalyScanSpec) -> AnomalyScanResult:
    if not spec.client_brand.strip():
        raise ValueError("client_brand is required")
    if spec.window_end <= spec.window_start:
        raise ValueError("window_end must be after window_start")

    observations = (
        list(spec.observations)
        if spec.observations
        else demo_observations(spec.window_end)
    )
    # Clip points to window
    clipped: list[MetricObservation] = []
    for obs in observations:
        pts = [
            (t, v)
            for t, v in obs.points
            if spec.window_start <= t <= spec.window_end
        ]
        if len(pts) >= 2:
            clipped.append(
                MetricObservation(
                    obs.metric_key,
                    obs.anomaly_type,
                    pts,
                    revenue_exposure=obs.revenue_exposure
                    if obs.revenue_exposure is not None
                    else (
                        spec.default_revenue_exposure or None
                    ),
                    label_hint=obs.label_hint,
                )
            )

    detected: list[AnomalyResult] = []
    for obs in clipped:
        hit = detect_on_series(obs)
        if hit:
            detected.append(hit)

    # Ensure we can still surface type coverage in demo even if one series weak
    # Rank by probable business impact
    detected.sort(
        key=lambda a: (a.impact_score, a.z_score, a.magnitude),
        reverse=True,
    )
    for i, a in enumerate(detected, start=1):
        # dataclasses with slots — recreate with rank
        detected[i - 1] = AnomalyResult(
            anomaly_type=a.anomaly_type,
            anomaly_label=a.anomaly_label,
            title=a.title,
            detail=a.detail,
            detected_at=a.detected_at,
            severity=a.severity,
            magnitude=a.magnitude,
            z_score=a.z_score,
            impact_score=a.impact_score,
            impact_rank=i,
            revenue_exposure=a.revenue_exposure,
            metric_key=a.metric_key,
            baseline_value=a.baseline_value,
            current_value=a.current_value,
            recommended_response=a.recommended_response,
            is_noise=a.is_noise,
        )

    critical = sum(1 for a in detected if a.severity == "critical")
    high = sum(1 for a in detected if a.severity == "high")
    top = detected[0] if detected else None
    summary = (
        f"Anomaly scan for {spec.client_brand}: {len(detected)} anomalies ranked by "
        f"probable business impact. "
        + (
            f"Top: {top.anomaly_label} (impact {top.impact_score}/100, {top.severity})."
            if top
            else "No anomalies cleared detection thresholds."
        )
    )
    return AnomalyScanResult(
        window_start=spec.window_start,
        window_end=spec.window_end,
        anomalies=detected,
        anomalies_detected=len(detected),
        critical_count=critical,
        high_count=high,
        top_anomaly_type=top.anomaly_type if top else None,
        top_impact_score=top.impact_score if top else None,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )


def catalog() -> dict[str, Any]:
    return {
        "anomaly_types": dict(ANOMALY_LABELS),
        "anomaly_codes": list(ANOMALY_TYPES),
        "severity_levels": list(SEVERITY_LEVELS),
        "impact_priors": dict(IMPACT_PRIORS),
        "methodology_note": METHODOLOGY_NOTE,
        "ranking_note": (
            "Anomalies are ranked by probable business impact using type priors, "
            "severity, signal strength, and optional revenue exposure."
        ),
    }
