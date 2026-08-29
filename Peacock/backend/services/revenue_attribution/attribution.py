"""Revenue attribution engine — funnel chain with uncertainty, no causal overclaim."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.revenue_attribution import (
    CAUSALITY_LEVELS,
    CAUSALITY_WARNING,
    DATA_SOURCES,
    FUNNEL_STAGES,
    METHODOLOGY_NOTE,
    SOURCE_LABELS,
    STAGE_LABELS,
)


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _clamp_rate(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class SourceAvailability:
    """Which integrations are available for this attribution run."""

    ga4: bool = False
    crm: bool = False
    search_console: bool = False
    conversions: bool = False
    pipeline: bool = False
    transactions: bool = False
    leads: bool = False
    peacock_internal: bool = True

    def available_codes(self) -> list[str]:
        mapping = {
            "ga4": self.ga4,
            "crm": self.crm,
            "search_console": self.search_console,
            "conversions": self.conversions,
            "pipeline": self.pipeline,
            "transactions": self.transactions,
            "leads": self.leads,
            "peacock_internal": self.peacock_internal,
        }
        return [k for k, v in mapping.items() if v]

    def missing_codes(self) -> list[str]:
        return [c for c in DATA_SOURCES if c not in self.available_codes()]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StageObservation:
    """Optional observed value at a funnel stage (ranges preferred)."""

    stage_code: str
    value_low: float
    value_high: float
    unit: str
    primary_source: str | None = None
    data_quality: float = 50.0
    notes: str | None = None

    def validate(self) -> None:
        if self.stage_code not in FUNNEL_STAGES:
            raise ValueError(f"Unknown stage_code: {self.stage_code}")
        if self.value_high < self.value_low:
            raise ValueError("value_high must be >= value_low")
        if not (0.0 <= self.data_quality <= 100.0):
            raise ValueError("data_quality must be 0–100")


@dataclass
class AttributionSpec:
    client_brand: str
    currency: str = "INR"
    horizon_days: int = 90
    sources: SourceAvailability = field(default_factory=SourceAvailability)
    observations: list[StageObservation] = field(default_factory=list)
    # Optional recommendation / content anchors
    recommendation_ref: str | None = None
    content_ref: str | None = None


@dataclass(slots=True)
class StageResult:
    stage_code: str
    stage_label: str
    sequence_order: int
    value_low: float
    value_high: float
    value_mid: float | None
    unit: str
    uncertainty: float
    data_quality: float
    primary_source: str | None
    notes: str | None
    display_band: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass(slots=True)
class ChainLinkResult:
    from_stage: str
    to_stage: str
    rate_low: float
    rate_high: float
    causality_level: str
    uncertainty: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SourceSnapshotResult:
    source_code: str
    source_label: str
    available: bool
    contribution_note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AttributionAnalysisResult:
    currency: str
    horizon_days: int
    stages: list[StageResult]
    links: list[ChainLinkResult]
    source_snapshots: list[SourceSnapshotResult]
    attributed_revenue_low: float
    attributed_revenue_high: float
    attributed_revenue_mid: float | None
    overall_causality_level: str
    overall_uncertainty: float
    data_completeness: float
    causality_warning: str
    methodology_note: str
    sources_available: list[str]
    sources_missing: list[str]
    funnel_path: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency": self.currency,
            "horizon_days": self.horizon_days,
            "stages": [s.to_dict() for s in self.stages],
            "links": [l.to_dict() for l in self.links],
            "source_snapshots": [s.to_dict() for s in self.source_snapshots],
            "attributed_revenue_low": self.attributed_revenue_low,
            "attributed_revenue_high": self.attributed_revenue_high,
            "attributed_revenue_mid": self.attributed_revenue_mid,
            "overall_causality_level": self.overall_causality_level,
            "overall_uncertainty": self.overall_uncertainty,
            "data_completeness": self.data_completeness,
            "causality_warning": self.causality_warning,
            "methodology_note": self.methodology_note,
            "sources_available": list(self.sources_available),
            "sources_missing": list(self.sources_missing),
            "funnel_path": list(self.funnel_path),
            "summary": self.summary,
        }


# Stage units and prior conversion-rate bands (low, high) between consecutive stages
_STAGE_UNITS: dict[str, str] = {
    "recommendation": "count",
    "content": "count",
    "visibility": "score_index",
    "traffic": "sessions",
    "lead": "count",
    "conversion": "count",
    "revenue": "currency",
}

_PRIOR_RATES: dict[tuple[str, str], tuple[float, float]] = {
    ("recommendation", "content"): (0.4, 0.85),
    ("content", "visibility"): (0.15, 0.55),
    ("visibility", "traffic"): (0.05, 0.35),
    ("traffic", "lead"): (0.01, 0.12),
    ("lead", "conversion"): (0.08, 0.45),
    ("conversion", "revenue"): (1.0, 1.0),  # identity scaled by AOV separately
}

_STAGE_SOURCE_HINTS: dict[str, tuple[str, ...]] = {
    "recommendation": ("peacock_internal",),
    "content": ("peacock_internal",),
    "visibility": ("search_console", "peacock_internal"),
    "traffic": ("ga4", "search_console"),
    "lead": ("crm", "leads", "ga4"),
    "conversion": ("conversions", "crm", "ga4"),
    "revenue": ("transactions", "pipeline", "crm"),
}


def _source_note(code: str, available: bool) -> str:
    if available:
        notes = {
            "ga4": "GA4 sessions/conversions available for traffic and conversion stages.",
            "crm": "CRM opportunities available for lead/pipeline linkage.",
            "search_console": "Search Console available for visibility/traffic proxies.",
            "conversions": "Conversion events available for conversion stage.",
            "pipeline": "Pipeline values available for revenue estimates.",
            "transactions": "Transaction revenue available for attributed revenue ranges.",
            "leads": "Lead records available for lead stage.",
            "peacock_internal": "Peacock recommendations/content/visibility signals available.",
        }
        return notes.get(code, f"{SOURCE_LABELS.get(code, code)} available.")
    return (
        f"{SOURCE_LABELS.get(code, code)} not connected — stage estimates use "
        "wider uncertainty and lower causality claims."
    )


def _pick_primary_source(stage: str, sources: SourceAvailability) -> str | None:
    for code in _STAGE_SOURCE_HINTS.get(stage, ()):
        if code in sources.available_codes():
            return code
    return None


def _base_stage_values(
    stage: str,
    sources: SourceAvailability,
    obs: StageObservation | None,
) -> tuple[float, float, float, str | None, str | None]:
    """Return (low, high, data_quality, primary_source, notes)."""
    if obs is not None:
        return (
            obs.value_low,
            obs.value_high,
            obs.data_quality,
            obs.primary_source or _pick_primary_source(stage, sources),
            obs.notes,
        )

    # Conservative priors when observation missing — wide bands
    priors = {
        "recommendation": (1.0, 3.0),
        "content": (1.0, 5.0),
        "visibility": (20.0, 55.0),
        "traffic": (100.0, 800.0),
        "lead": (2.0, 40.0),
        "conversion": (0.5, 12.0),
        "revenue": (5_000.0, 80_000.0),
    }
    lo, hi = priors[stage]
    dq = 35.0
    primary = _pick_primary_source(stage, sources)
    if primary:
        dq += 20.0
        # Narrow slightly when a relevant source is present
        mid = (lo + hi) / 2.0
        lo = mid - (mid - lo) * 0.75
        hi = mid + (hi - mid) * 0.75
    notes = (
        f"Estimated prior for {STAGE_LABELS[stage]} "
        f"(no direct observation; uncertainty elevated)."
    )
    return lo, hi, _clamp100(dq), primary, notes


def _rate_for_link(
    from_s: str,
    to_s: str,
    from_vals: tuple[float, float],
    to_vals: tuple[float, float],
    sources: SourceAvailability,
) -> tuple[float, float, float, str]:
    """Derive conversion-rate band and uncertainty between stages."""
    prior_lo, prior_hi = _PRIOR_RATES[(from_s, to_s)]
    # Implied rates from values when both ends known
    f_lo, f_hi = from_vals
    t_lo, t_hi = to_vals
    if f_hi > 0 and from_s != "conversion":
        implied_lo = _clamp_rate(t_lo / f_hi) if f_hi else prior_lo
        implied_hi = _clamp_rate(t_hi / max(f_lo, 1e-6)) if f_lo else prior_hi
        if implied_hi < implied_lo:
            implied_lo, implied_hi = implied_hi, implied_lo
        # Blend prior with implied
        lo = (prior_lo + implied_lo) / 2.0
        hi = (prior_hi + implied_hi) / 2.0
    else:
        lo, hi = prior_lo, prior_hi

    # Widen when key sources missing
    missing_penalty = 0.0
    needed = set(_STAGE_SOURCE_HINTS.get(from_s, ())) | set(
        _STAGE_SOURCE_HINTS.get(to_s, ())
    )
    avail = set(sources.available_codes())
    missing = needed - avail
    missing_penalty = 12.0 * len(missing)
    width = hi - lo
    lo = max(0.0, lo - width * 0.1 * (missing_penalty / 20.0))
    hi = min(1.0 if to_s != "revenue" else hi * 1.1, hi + width * 0.15 * (1 + missing_penalty / 30.0))
    if to_s == "revenue":
        # revenue link is value multiplier context; keep as 1.0 identity for counts→currency handled at stage
        lo, hi = 1.0, 1.0
    uncertainty = _clamp100(40.0 + missing_penalty + width * 80.0)
    return round(lo, 4), round(hi, 4), uncertainty, (
        f"Rate band {lo:.1%}–{hi:.1%} for {STAGE_LABELS[from_s]} → {STAGE_LABELS[to_s]}; "
        f"missing sources {sorted(missing) or ['none']} increase uncertainty."
    )


def _causality_for_link(
    from_s: str,
    to_s: str,
    sources: SourceAvailability,
    uncertainty: float,
) -> str:
    avail = set(sources.available_codes())
    needed = set(_STAGE_SOURCE_HINTS.get(from_s, ())) | set(
        _STAGE_SOURCE_HINTS.get(to_s, ())
    )
    overlap = needed & avail
    if not overlap and from_s not in ("recommendation", "content"):
        return "insufficient_data"
    if uncertainty >= 70:
        return "correlation"
    # Multi-touch only when CRM + GA4 + conversions-ish present toward bottom funnel
    if {from_s, to_s} & {"lead", "conversion", "revenue"}:
        if {"ga4", "crm"}.issubset(avail) or {"transactions", "conversions"}.issubset(avail):
            return "multi_touch_model"
        if overlap:
            return "likely_contribution"
        return "correlation"
    if overlap:
        return "likely_contribution"
    return "correlation"


def _overall_causality(links: list[ChainLinkResult], completeness: float) -> str:
    levels = [l.causality_level for l in links]
    if completeness < 30 or "insufficient_data" in levels:
        return "insufficient_data"
    if all(l == "multi_touch_model" for l in levels[-2:]):
        return "multi_touch_model"
    if "likely_contribution" in levels or "multi_touch_model" in levels:
        return "likely_contribution"
    # Never default to causal_evidence from visibility→revenue alone
    if "causal_evidence" in levels:
        return "likely_contribution"  # downgrade — do not overclaim
    return "correlation"


def attribute_revenue(spec: AttributionSpec) -> AttributionAnalysisResult:
    """Build Recommendation→…→Revenue chain with uncertainty ranges."""
    if not spec.client_brand.strip():
        raise ValueError("client_brand is required")
    if spec.horizon_days <= 0:
        raise ValueError("horizon_days must be positive")

    for o in spec.observations:
        o.validate()
    obs_map = {o.stage_code: o for o in spec.observations}
    sources = spec.sources

    stage_vals: dict[str, tuple[float, float]] = {}
    stages: list[StageResult] = []

    for i, code in enumerate(FUNNEL_STAGES, start=1):
        lo, hi, dq, primary, notes = _base_stage_values(code, sources, obs_map.get(code))
        if code == "recommendation" and spec.recommendation_ref:
            notes = (notes or "") + f" Anchor: {spec.recommendation_ref}."
        if code == "content" and spec.content_ref:
            notes = (notes or "") + f" Content: {spec.content_ref}."
        # Ensure minimum band width (no fake precision)
        if hi - lo < max(0.01 * max(abs(hi), 1.0), 0.01):
            mid = (lo + hi) / 2.0
            lo, hi = mid * 0.9, mid * 1.1
        uncertainty = _clamp100(100.0 - dq + (hi - lo) / max(abs(hi), 1.0) * 40.0)
        mid = round((lo + hi) / 2.0, 2)
        stage_vals[code] = (lo, hi)
        unit = _STAGE_UNITS[code] if code != "revenue" else spec.currency
        if code == "revenue":
            display = f"{lo:,.0f}–{hi:,.0f} {spec.currency}"
        else:
            display = f"{lo:,.1f}–{hi:,.1f} {unit}"
        stages.append(
            StageResult(
                stage_code=code,
                stage_label=STAGE_LABELS[code],
                sequence_order=i,
                value_low=round(lo, 2),
                value_high=round(hi, 2),
                value_mid=mid,
                unit=unit,
                uncertainty=round(uncertainty, 1),
                data_quality=round(dq, 1),
                primary_source=primary,
                notes=notes,
                display_band=display,
            )
        )

    links: list[ChainLinkResult] = []
    for a, b in zip(FUNNEL_STAGES, FUNNEL_STAGES[1:]):
        rate_lo, rate_hi, unc, rationale = _rate_for_link(
            a, b, stage_vals[a], stage_vals[b], sources
        )
        causality = _causality_for_link(a, b, sources, unc)
        # Hard rule: never emit causal_evidence from this engine alone
        if causality == "causal_evidence":
            causality = "likely_contribution"
            rationale += " Downgraded from causal_evidence — do not overclaim."
        assert causality in CAUSALITY_LEVELS
        links.append(
            ChainLinkResult(
                from_stage=a,
                to_stage=b,
                rate_low=rate_lo,
                rate_high=rate_hi,
                causality_level=causality,
                uncertainty=round(unc, 1),
                rationale=rationale,
            )
        )

    rev = next(s for s in stages if s.stage_code == "revenue")
    avail = sources.available_codes()
    missing = sources.missing_codes()
    completeness = _clamp100(100.0 * len(avail) / max(len(DATA_SOURCES), 1))
    overall_unc = _clamp100(
        sum(s.uncertainty for s in stages) / max(len(stages), 1)
    )
    overall_causality = _overall_causality(links, completeness)

    snapshots = [
        SourceSnapshotResult(
            source_code=code,
            source_label=SOURCE_LABELS[code],
            available=code in avail,
            contribution_note=_source_note(code, code in avail),
        )
        for code in DATA_SOURCES
    ]

    funnel_path = [STAGE_LABELS[c] for c in FUNNEL_STAGES]
    summary = (
        f"Revenue attribution for {spec.client_brand} over {spec.horizon_days} days: "
        f"attributed revenue {rev.display_band} with uncertainty {overall_unc:.0f}/100; "
        f"causality level '{overall_causality}' (not a causal guarantee). "
        f"Sources available: {', '.join(avail) or 'none'}; missing: {', '.join(missing) or 'none'}. "
        f"{CAUSALITY_WARNING}"
    )

    return AttributionAnalysisResult(
        currency=spec.currency,
        horizon_days=spec.horizon_days,
        stages=stages,
        links=links,
        source_snapshots=snapshots,
        attributed_revenue_low=rev.value_low,
        attributed_revenue_high=rev.value_high,
        attributed_revenue_mid=rev.value_mid,
        overall_causality_level=overall_causality,
        overall_uncertainty=round(overall_unc, 1),
        data_completeness=round(completeness, 1),
        causality_warning=CAUSALITY_WARNING,
        methodology_note=METHODOLOGY_NOTE,
        sources_available=avail,
        sources_missing=missing,
        funnel_path=funnel_path,
        summary=summary,
    )
