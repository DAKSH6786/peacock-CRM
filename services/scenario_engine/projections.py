"""Peacock Scenario Engine — counterfactual projections as ranges (not fake precision)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.scenario_engine import (
    DEFAULT_METRIC,
    DEFAULT_METRIC_LABEL,
    METHODOLOGY_NOTE,
    RANGES_NOT_FAKE_PRECISION,
    STRATEGY_CODES,
    STRATEGY_LABELS,
)


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _clamp_pct(value: float, lo: float = -20.0, hi: float = 80.0) -> float:
    return max(lo, min(hi, float(value)))


@dataclass
class ContextSignals:
    """Observed context that widens/narrows ranges and confidence.

    Defaults are neutral so catalog/example priors (Baseline +0–4%, Content
    Expansion +7–18%, Authority +9–22%, Peacock +14–31%) hold until inputs deviate.
    """

    technical_seo_health: float = 70.0  # 0–100; gap below 70 lifts fix_technical_seo
    content_velocity: float = 50.0
    content_freshness: float = 70.0
    topical_coverage: float = 70.0
    third_party_authority: float = 70.0
    seo_demand: float = 50.0
    geo_opportunity: float = 50.0
    aeo_opportunity: float = 50.0
    data_quality: float = 70.0  # overall input quality
    competitor_pressure: float = 50.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AssumptionInput:
    assumption_key: str
    statement: str
    sensitivity: str = "medium"
    affects_strategies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assumption_key": self.assumption_key,
            "statement": self.statement,
            "sensitivity": self.sensitivity,
            "affects_strategies": list(self.affects_strategies),
        }


@dataclass
class ScenarioSpec:
    client_brand: str
    horizon_days: int = 90
    primary_metric: str = DEFAULT_METRIC
    primary_metric_label: str = DEFAULT_METRIC_LABEL
    context: ContextSignals = field(default_factory=ContextSignals)
    assumptions: list[AssumptionInput] = field(default_factory=list)
    strategies: list[str] = field(default_factory=list)  # empty = all
    extra_metrics: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class MetricRangeResult:
    metric_code: str
    metric_label: str
    range_low_pct: float
    range_high_pct: float
    unit: str = "percent_change"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def format_band(self) -> str:
        return f"{self.range_low_pct:+.0f}% to {self.range_high_pct:+.0f}%"


@dataclass(slots=True)
class ScenarioResult:
    strategy_code: str
    strategy_label: str
    is_baseline: bool
    is_peacock_recommended: bool
    range_low_pct: float
    range_high_pct: float
    range_mid_pct: float | None
    confidence: float
    data_quality: float
    uncertainty: float
    rationale: str
    rank: int
    metric_ranges: list[MetricRangeResult]
    display_band: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_code": self.strategy_code,
            "strategy_label": self.strategy_label,
            "is_baseline": self.is_baseline,
            "is_peacock_recommended": self.is_peacock_recommended,
            "range_low_pct": self.range_low_pct,
            "range_high_pct": self.range_high_pct,
            "range_mid_pct": self.range_mid_pct,
            "confidence": self.confidence,
            "data_quality": self.data_quality,
            "uncertainty": self.uncertainty,
            "rationale": self.rationale,
            "rank": self.rank,
            "metric_ranges": [m.to_dict() for m in self.metric_ranges],
            "display_band": self.display_band,
        }


@dataclass(slots=True)
class AssumptionResult:
    assumption_key: str
    statement: str
    sensitivity: str
    affects_strategies: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScenarioAnalysisResult:
    horizon_days: int
    primary_metric: str
    primary_metric_label: str
    scenarios: list[ScenarioResult]
    assumptions: list[AssumptionResult]
    overall_confidence: float
    overall_data_quality: float
    overall_uncertainty: float
    assumptions_summary: str
    ranges_not_fake_precision: bool
    ranges_disclaimer: str
    methodology_note: str
    recommended_strategy_code: str
    comparison_table: list[dict[str, str]]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "horizon_days": self.horizon_days,
            "primary_metric": self.primary_metric,
            "primary_metric_label": self.primary_metric_label,
            "scenarios": [s.to_dict() for s in self.scenarios],
            "assumptions": [a.to_dict() for a in self.assumptions],
            "overall_confidence": self.overall_confidence,
            "overall_data_quality": self.overall_data_quality,
            "overall_uncertainty": self.overall_uncertainty,
            "assumptions_summary": self.assumptions_summary,
            "ranges_not_fake_precision": self.ranges_not_fake_precision,
            "ranges_disclaimer": self.ranges_disclaimer,
            "methodology_note": self.methodology_note,
            "recommended_strategy_code": self.recommended_strategy_code,
            "comparison_table": list(self.comparison_table),
            "summary": self.summary,
        }


# Base range priors (low, high) for 90d organic visibility % change — intentionally wide
_BASE_RANGES: dict[str, tuple[float, float]] = {
    "do_nothing": (0.0, 4.0),
    "fix_technical_seo": (3.0, 12.0),
    "publish_more_content": (7.0, 18.0),
    "refresh_existing_content": (5.0, 15.0),
    "build_topical_authority": (8.0, 20.0),
    "build_third_party_authority": (9.0, 22.0),
    "seo_only": (6.0, 16.0),
    "geo_only": (5.0, 17.0),
    "seo_aeo_geo": (11.0, 26.0),
    "peacock_recommended": (14.0, 31.0),
}


def _adjust_range(
    strategy: str,
    lo: float,
    hi: float,
    ctx: ContextSignals,
) -> tuple[float, float]:
    """Shift/widen ranges from context — never collapse to a point."""
    # Headroom adjustments
    if strategy == "fix_technical_seo":
        gap = max(0.0, 70.0 - ctx.technical_seo_health) / 100.0
        lo += 2.0 * gap
        hi += 6.0 * gap
    if strategy == "publish_more_content":
        lo += (ctx.content_velocity - 50.0) * 0.04
        hi += (ctx.seo_demand - 50.0) * 0.08
    if strategy == "refresh_existing_content":
        stale = max(0.0, 70.0 - ctx.content_freshness) / 100.0
        lo += 3.0 * stale
        hi += 8.0 * stale
    if strategy == "build_topical_authority":
        gap = max(0.0, 70.0 - ctx.topical_coverage) / 100.0
        lo += 3.0 * gap
        hi += 7.0 * gap
    if strategy == "build_third_party_authority":
        gap = max(0.0, 70.0 - ctx.third_party_authority) / 100.0
        lo += 2.5 * gap
        hi += 8.0 * gap
    if strategy == "seo_only":
        lo += (ctx.seo_demand - 50.0) * 0.05
        hi += (ctx.seo_demand - 50.0) * 0.1
    if strategy == "geo_only":
        lo += (ctx.geo_opportunity - 50.0) * 0.06
        hi += (ctx.geo_opportunity - 50.0) * 0.12
    if strategy in ("seo_aeo_geo", "peacock_recommended"):
        blend = (
            (ctx.seo_demand + ctx.aeo_opportunity + ctx.geo_opportunity) / 3.0 - 50.0
        ) * 0.08
        lo += blend * 0.6
        hi += blend

    # Competitor pressure widens uncertainty (raise high less than low)
    pressure = (ctx.competitor_pressure - 50.0) / 100.0
    lo -= 2.0 * max(0.0, pressure)
    hi += 3.0 * abs(pressure)

    # Poor data quality widens band
    dq_gap = max(0.0, 70.0 - ctx.data_quality) / 100.0
    lo -= 2.0 * dq_gap
    hi += 4.0 * dq_gap

    lo = _clamp_pct(lo)
    hi = _clamp_pct(hi)
    if hi - lo < 3.0:
        # Enforce non-fake-precision: keep a minimum band width
        mid = (lo + hi) / 2.0
        lo = _clamp_pct(mid - 1.5)
        hi = _clamp_pct(mid + 1.5)
    if hi < lo:
        lo, hi = hi, lo
    return round(lo, 1), round(hi, 1)


def _scenario_confidence(strategy: str, ctx: ContextSignals, band_width: float) -> float:
    base = 0.45 * ctx.data_quality + 0.25 * (100.0 - min(band_width * 3, 100.0))
    # Baseline more confident (narrower theory); peacock slightly less (more moving parts)
    if strategy == "do_nothing":
        base += 10.0
    if strategy == "peacock_recommended":
        base -= 5.0
    if strategy in ("geo_only", "seo_aeo_geo"):
        base += (ctx.geo_opportunity - 50.0) * 0.1
    return _clamp100(base + 20.0)


def _scenario_uncertainty(band_width: float, data_quality: float) -> float:
    return _clamp100(band_width * 2.5 + (100.0 - data_quality) * 0.35)


def _default_assumptions(ctx: ContextSignals) -> list[AssumptionResult]:
    return [
        AssumptionResult(
            assumption_key="stable_engine_behavior",
            statement=(
                "Search and generative-engine retrieval behavior remain roughly stable "
                "over the projection horizon."
            ),
            sensitivity="high",
            affects_strategies=list(STRATEGY_CODES),
        ),
        AssumptionResult(
            assumption_key="execution_fidelity",
            statement=(
                "Strategy execution quality matches historical Peacock delivery norms "
                f"(technical SEO health prior {ctx.technical_seo_health:.0f}/100)."
            ),
            sensitivity="high",
            affects_strategies=[
                "fix_technical_seo",
                "publish_more_content",
                "refresh_existing_content",
                "seo_aeo_geo",
                "peacock_recommended",
            ],
        ),
        AssumptionResult(
            assumption_key="no_major_algorithm_shock",
            statement="No discontinuous ranking or citation algorithm shock in-horizon.",
            sensitivity="medium",
            affects_strategies=list(STRATEGY_CODES),
        ),
        AssumptionResult(
            assumption_key="ranges_not_guarantees",
            statement=RANGES_NOT_FAKE_PRECISION,
            sensitivity="high",
            affects_strategies=list(STRATEGY_CODES),
        ),
    ]


def _extra_metric_range(
    strategy: str,
    metric_code: str,
    metric_label: str,
    primary_lo: float,
    primary_hi: float,
) -> MetricRangeResult:
    # Correlate extras loosely with primary, keep as ranges
    scale = {
        "ai_citation_lift_90d": 0.85,
        "aeo_answer_presence_90d": 0.7,
        "engagement_90d": 0.6,
    }.get(metric_code, 0.75)
    lo = round(_clamp_pct(primary_lo * scale - 1.0), 1)
    hi = round(_clamp_pct(primary_hi * scale + 1.0), 1)
    if strategy == "do_nothing":
        lo, hi = 0.0, max(2.0, hi * 0.3)
    return MetricRangeResult(
        metric_code=metric_code,
        metric_label=metric_label,
        range_low_pct=lo,
        range_high_pct=max(lo + 2.0, hi),
    )


def run_scenario_analysis(spec: ScenarioSpec) -> ScenarioAnalysisResult:
    """Compare counterfactual strategies with projected ranges."""
    if not spec.client_brand.strip():
        raise ValueError("client_brand is required")
    if spec.horizon_days <= 0:
        raise ValueError("horizon_days must be positive")

    strategies = list(spec.strategies) if spec.strategies else list(STRATEGY_CODES)
    for s in strategies:
        if s not in STRATEGY_CODES:
            raise ValueError(f"Unsupported strategy_code: {s}")
    # Ensure baseline + peacock present for comparison quality
    if "do_nothing" not in strategies:
        strategies = ["do_nothing", *strategies]
    if "peacock_recommended" not in strategies:
        strategies = [*strategies, "peacock_recommended"]

    ctx = spec.context
    scenarios: list[ScenarioResult] = []

    for code in strategies:
        base_lo, base_hi = _BASE_RANGES[code]
        # Scale mildly if horizon != 90
        horizon_scale = spec.horizon_days / 90.0
        lo, hi = _adjust_range(
            code, base_lo * horizon_scale, base_hi * horizon_scale, ctx
        )
        width = hi - lo
        confidence = _scenario_confidence(code, ctx, width)
        uncertainty = _scenario_uncertainty(width, ctx.data_quality)
        mid = round((lo + hi) / 2.0, 1)  # display only
        extras = [
            _extra_metric_range(code, m, label, lo, hi)
            for m, label in spec.extra_metrics
        ]
        scenarios.append(
            ScenarioResult(
                strategy_code=code,
                strategy_label=STRATEGY_LABELS[code],
                is_baseline=(code == "do_nothing"),
                is_peacock_recommended=(code == "peacock_recommended"),
                range_low_pct=lo,
                range_high_pct=hi,
                range_mid_pct=mid,
                confidence=confidence,
                data_quality=_clamp100(ctx.data_quality),
                uncertainty=uncertainty,
                rationale=(
                    f"{STRATEGY_LABELS[code]} projects a {lo:+.0f}% to {hi:+.0f}% "
                    f"{spec.primary_metric_label} range over {spec.horizon_days} days "
                    f"(not a point forecast). Uncertainty {uncertainty:.0f}/100."
                ),
                rank=0,
                metric_ranges=extras,
                display_band=f"{lo:+.0f}% to {hi:+.0f}%",
            )
        )

    # Rank by optimistic high, then low — peacock should typically lead in example priors
    scenarios.sort(key=lambda s: (s.range_high_pct, s.range_low_pct), reverse=True)
    for i, s in enumerate(scenarios, start=1):
        s.rank = i

    if spec.assumptions:
        assumptions = [
            AssumptionResult(
                assumption_key=a.assumption_key,
                statement=a.statement,
                sensitivity=a.sensitivity,
                affects_strategies=list(a.affects_strategies) or list(STRATEGY_CODES),
            )
            for a in spec.assumptions
        ]
    else:
        assumptions = _default_assumptions(ctx)

    overall_dq = _clamp100(ctx.data_quality)
    overall_unc = _clamp100(
        sum(s.uncertainty for s in scenarios) / max(1, len(scenarios))
    )
    overall_conf = _clamp100(
        sum(s.confidence for s in scenarios) / max(1, len(scenarios))
    )
    assumptions_summary = (
        f"{len(assumptions)} explicit assumption(s). "
        + "; ".join(a.statement for a in assumptions[:3])
    )

    comparison_table = [
        {
            "strategy": s.strategy_label,
            "projected_range": s.display_band,
            "confidence": f"{s.confidence:.0f}/100",
            "uncertainty": f"{s.uncertainty:.0f}/100",
            "data_quality": f"{s.data_quality:.0f}/100",
        }
        for s in sorted(scenarios, key=lambda x: x.strategy_code != "do_nothing")
    ]
    # Prefer a readable order matching the product example
    preferred_order = [
        "do_nothing",
        "publish_more_content",
        "build_third_party_authority",
        "peacock_recommended",
    ]
    ordered = []
    by_code = {s.strategy_code: s for s in scenarios}
    for code in preferred_order:
        if code in by_code:
            ordered.append(
                {
                    "strategy": by_code[code].strategy_label,
                    "projected_range": by_code[code].display_band,
                }
            )
    for s in scenarios:
        if s.strategy_code not in preferred_order:
            ordered.append(
                {"strategy": s.strategy_label, "projected_range": s.display_band}
            )

    peacock = by_code.get("peacock_recommended")
    summary = (
        f"Counterfactual comparison for {spec.client_brand} over {spec.horizon_days} days. "
        f"{spec.primary_metric_label} ranges (not fake precision). "
        + (
            f"Peacock Strategy: {peacock.display_band}. "
            if peacock
            else ""
        )
        + f"Overall confidence {overall_conf:.0f}/100, data quality {overall_dq:.0f}/100, "
        f"uncertainty {overall_unc:.0f}/100."
    )

    return ScenarioAnalysisResult(
        horizon_days=spec.horizon_days,
        primary_metric=spec.primary_metric,
        primary_metric_label=spec.primary_metric_label,
        scenarios=scenarios,
        assumptions=assumptions,
        overall_confidence=overall_conf,
        overall_data_quality=overall_dq,
        overall_uncertainty=overall_unc,
        assumptions_summary=assumptions_summary,
        ranges_not_fake_precision=True,
        ranges_disclaimer=RANGES_NOT_FAKE_PRECISION,
        methodology_note=METHODOLOGY_NOTE,
        recommended_strategy_code="peacock_recommended",
        comparison_table=ordered,
        summary=summary,
    )
