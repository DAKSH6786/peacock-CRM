"""GEO Lab analysis — deltas, time series, cautious causality (never auto-causal)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any

from db_models.geo_lab import (
    CAUSALITY_LEVELS,
    CAUSALITY_WARNING,
    GEO_LAB_METRICS,
    VARIANT_PRESETS,
)


def _safe_mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(mean(values))


def _rel_pct(pre: float, post: float) -> float | None:
    if pre == 0:
        return None if post == 0 else 100.0
    return ((post - pre) / abs(pre)) * 100.0


@dataclass
class VariantSpec:
    variant_code: str
    label: str | None = None
    treatment_description: str | None = None
    is_baseline: bool = False
    change_summary: str | None = None

    def resolved_label(self) -> str:
        if self.label:
            return self.label
        preset = VARIANT_PRESETS.get(self.variant_code.upper())
        return preset.replace("_", " ").title() if preset else f"Variant {self.variant_code}"

    def resolved_treatment(self) -> str:
        if self.treatment_description:
            return self.treatment_description
        preset = VARIANT_PRESETS.get(self.variant_code.upper(), "custom treatment")
        return f"Treatment: {preset.replace('_', ' ')}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_code": self.variant_code,
            "label": self.resolved_label(),
            "treatment_description": self.resolved_treatment(),
            "is_baseline": self.is_baseline,
            "change_summary": self.change_summary,
        }


@dataclass
class PageSpec:
    url: str
    page_role: str  # control|test
    variant_code: str | None = None
    title: str | None = None
    matched_group: str | None = None
    match_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ObservationSpec:
    page_url: str
    metric_code: str
    observed_at: str
    period: str  # pre|post|during
    value: float
    engine: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MetricDeltaResult:
    scope_type: str
    scope_id: str
    metric_code: str
    pre_mean: float
    post_mean: float
    absolute_delta: float
    relative_delta_pct: float | None
    control_adjusted_delta: float | None
    observation_count_pre: int
    observation_count_post: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CausalityAssessmentResult:
    metric_code: str
    variant_code: str
    causality_level: str
    claim_allowed: bool
    auto_causal_conclusion_rejected: bool
    rationale: str
    confounds_noted: str | None
    design_supports: list[str]
    confidence_note: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["design_supports"] = list(self.design_supports)
        return d


@dataclass(slots=True)
class TimeSeriesPoint:
    observed_at: str
    period: str
    metric_code: str
    scope_type: str
    scope_id: str
    value: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExperimentAnalysisInput:
    variants: list[VariantSpec]
    pages: list[PageSpec]
    observations: list[ObservationSpec]
    known_confounds: list[str] = field(default_factory=list)
    concurrent_changes: list[str] = field(default_factory=list)


@dataclass
class ExperimentAnalysisResult:
    deltas: list[MetricDeltaResult]
    causality_assessments: list[CausalityAssessmentResult]
    time_series: list[TimeSeriesPoint]
    overall_causality_level: str
    overall_summary: str
    causality_warning: str = CAUSALITY_WARNING
    design_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "deltas": [d.to_dict() for d in self.deltas],
            "causality_assessments": [c.to_dict() for c in self.causality_assessments],
            "time_series": [t.to_dict() for t in self.time_series],
            "overall_causality_level": self.overall_causality_level,
            "overall_summary": self.overall_summary,
            "causality_warning": self.causality_warning,
            "design_features": list(self.design_features),
        }


def default_variants() -> list[VariantSpec]:
    """Canonical A/B/C/D GEO Lab variants."""
    return [
        VariantSpec(
            variant_code="A",
            label="Original page",
            treatment_description="Version A — Original page (baseline / control treatment).",
            is_baseline=True,
            change_summary="No intentional content change.",
        ),
        VariantSpec(
            variant_code="B",
            label="Improved evidence",
            treatment_description="Version B — Improved evidence (citations, stats, sources).",
            change_summary="Add stronger evidence density and attribution.",
        ),
        VariantSpec(
            variant_code="C",
            label="Better structured answers",
            treatment_description="Version C — Better structured answers (FAQ, definitions, direct answers).",
            change_summary="Improve answer structure for AEO/GEO retrieval.",
        ),
        VariantSpec(
            variant_code="D",
            label="Original dataset added",
            treatment_description="Version D — Original dataset added (first-party data / study).",
            change_summary="Publish original dataset or proprietary numbers.",
        ),
    ]


def _period_means(
    observations: list[ObservationSpec],
    *,
    page_urls: set[str],
    metric: str,
) -> tuple[float | None, float | None, int, int]:
    pre = [
        o.value
        for o in observations
        if o.page_url in page_urls and o.metric_code == metric and o.period == "pre"
    ]
    post = [
        o.value
        for o in observations
        if o.page_url in page_urls and o.metric_code == metric and o.period == "post"
    ]
    return _safe_mean(pre), _safe_mean(post), len(pre), len(post)


def _design_features(pages: list[PageSpec], observations: list[ObservationSpec]) -> list[str]:
    features: list[str] = ["before_after"]
    roles = {p.page_role for p in pages}
    if "control" in roles:
        features.append("control_pages")
    if "test" in roles:
        features.append("test_pages")
    if any(p.matched_group for p in pages):
        features.append("matched_groups")
    dates = {o.observed_at for o in observations}
    if len(dates) >= 3:
        features.append("time_series")
    return features


def classify_causality(
    *,
    metric_code: str,
    variant_code: str,
    test_delta: float,
    control_delta: float | None,
    control_adjusted_delta: float | None,
    design_features: list[str],
    n_pre: int,
    n_post: int,
    known_confounds: list[str],
    concurrent_changes: list[str],
) -> CausalityAssessmentResult:
    """Classify evidence strength — NEVER returns automatic causal conclusion as claim_allowed True for 'caused'."""

    supports = list(design_features)
    confounds = list(known_confounds) + list(concurrent_changes)
    has_control = "control_pages" in design_features
    has_matched = "matched_groups" in design_features
    has_ts = "time_series" in design_features
    sufficient_n = n_pre >= 2 and n_post >= 2

    # Start at correlation — always reject auto causal conclusion
    level = "correlation"
    rationale_parts = [
        f"Observed before/after change on {metric_code} for variant {variant_code} "
        f"(Δ={test_delta:+.3f})."
    ]

    if has_control and control_adjusted_delta is not None:
        rationale_parts.append(
            f"Control-adjusted delta={control_adjusted_delta:+.3f} "
            f"(test Δ={test_delta:+.3f}, control Δ={control_delta:+.3f})."
        )
        # Lift vs control suggests contribution but not proof
        if abs(control_adjusted_delta) > 0.01 and sufficient_n:
            level = "likely_contribution"
            rationale_parts.append(
                "Test pages moved differently from controls — treated as likely contribution, "
                "not proof of causation."
            )

    if has_control and has_matched and sufficient_n and control_adjusted_delta is not None:
        if abs(control_adjusted_delta) > abs(test_delta) * 0.2 or abs(control_adjusted_delta) > 0.05:
            level = "controlled_experiment"
            rationale_parts.append(
                "Design includes control pages and matched groups with before/after windows — "
                "classified as controlled experiment evidence."
            )

    # Causal evidence requires strong design AND no major confounds AND time series
    # Even then, claim_allowed stays False for absolute "X caused Y" language
    if (
        level == "controlled_experiment"
        and has_ts
        and sufficient_n
        and not concurrent_changes
        and len(known_confounds) == 0
        and control_adjusted_delta is not None
        and abs(control_adjusted_delta) > 0.05
    ):
        level = "causal_evidence"
        rationale_parts.append(
            "Strongest available label in GEO Lab: causal_evidence. This still does NOT "
            "authorize an automatic claim that Change X caused the visibility improvement; "
            "residual bias and engine-side changes may remain."
        )

    if confounds:
        rationale_parts.append("Confounds / concurrent changes noted: " + "; ".join(confounds[:8]))
        # Downgrade if we had reached causal_evidence
        if level == "causal_evidence":
            level = "controlled_experiment"
            rationale_parts.append(
                "Downgraded from causal_evidence because confounds or concurrent changes exist."
            )

    if not has_control:
        rationale_parts.append(
            "No control pages — cannot separate treatment from market/engine drift; "
            "capped at correlation or weak likely contribution."
        )
        if level in ("controlled_experiment", "causal_evidence"):
            level = "likely_contribution" if sufficient_n else "correlation"
        elif level == "likely_contribution" and not sufficient_n:
            level = "correlation"

    # claim_allowed: only soft interpretive claims, never "X caused Y"
    claim_allowed = level in (
        "likely_contribution",
        "controlled_experiment",
        "causal_evidence",
    )

    confidence_note = (
        "Peacock refuses automatic causal slogans. Prefer: "
        f"«{level.replace('_', ' ')}» for {metric_code} / variant {variant_code}. "
        "Do not state that the treatment caused the lift without human review."
    )

    assert level in CAUSALITY_LEVELS

    return CausalityAssessmentResult(
        metric_code=metric_code,
        variant_code=variant_code,
        causality_level=level,
        claim_allowed=claim_allowed,
        auto_causal_conclusion_rejected=True,
        rationale=" ".join(rationale_parts),
        confounds_noted="; ".join(confounds) if confounds else None,
        design_supports=supports,
        confidence_note=confidence_note,
    )


def analyse_experiment(inp: ExperimentAnalysisInput) -> ExperimentAnalysisResult:
    """Compute before/after deltas, time series aggregates, and cautious causality."""
    if not inp.pages:
        raise ValueError("At least one page (control or test) is required")
    if not inp.observations:
        raise ValueError("At least one metric observation is required")

    metrics_present = sorted({o.metric_code for o in inp.observations})
    for m in metrics_present:
        if m not in GEO_LAB_METRICS:
            raise ValueError(f"Unsupported metric_code: {m}")

    design = _design_features(inp.pages, inp.observations)
    pages_by_url = {p.url: p for p in inp.pages}
    control_urls = {p.url for p in inp.pages if p.page_role == "control"}
    test_urls = {p.url for p in inp.pages if p.page_role == "test"}

    deltas: list[MetricDeltaResult] = []

    def add_scope_delta(
        scope_type: str,
        scope_id: str,
        urls: set[str],
        metric: str,
        control_delta: float | None = None,
    ) -> MetricDeltaResult | None:
        pre_m, post_m, n_pre, n_post = _period_means(
            inp.observations, page_urls=urls, metric=metric
        )
        if pre_m is None or post_m is None:
            return None
        abs_d = post_m - pre_m
        adj = None
        if control_delta is not None:
            adj = abs_d - control_delta
        result = MetricDeltaResult(
            scope_type=scope_type,
            scope_id=scope_id,
            metric_code=metric,
            pre_mean=pre_m,
            post_mean=post_m,
            absolute_delta=abs_d,
            relative_delta_pct=_rel_pct(pre_m, post_m),
            control_adjusted_delta=adj,
            observation_count_pre=n_pre,
            observation_count_post=n_post,
        )
        deltas.append(result)
        return result

    # Control pool deltas first (no adjustment)
    control_deltas_by_metric: dict[str, float] = {}
    for metric in metrics_present:
        if control_urls:
            cd = add_scope_delta("control_pool", "all_controls", control_urls, metric)
            if cd:
                control_deltas_by_metric[metric] = cd.absolute_delta

        if test_urls:
            add_scope_delta(
                "test_pool",
                "all_tests",
                test_urls,
                metric,
                control_delta=control_deltas_by_metric.get(metric),
            )

        # Per-page
        for page in inp.pages:
            add_scope_delta(
                "page",
                page.url,
                {page.url},
                metric,
                control_delta=control_deltas_by_metric.get(metric)
                if page.page_role == "test"
                else None,
            )

        # Per variant (test pages for that variant)
        variant_codes = {v.variant_code for v in inp.variants} | {
            p.variant_code for p in inp.pages if p.variant_code
        }
        for vc in sorted(c for c in variant_codes if c):
            urls = {
                p.url
                for p in inp.pages
                if p.variant_code == vc and p.page_role == "test"
            }
            if not urls:
                urls = {p.url for p in inp.pages if p.variant_code == vc}
            if urls:
                add_scope_delta(
                    "variant",
                    vc,
                    urls,
                    metric,
                    control_delta=control_deltas_by_metric.get(metric),
                )

        # Matched groups
        groups = {p.matched_group for p in inp.pages if p.matched_group}
        for g in sorted(groups):
            urls = {p.url for p in inp.pages if p.matched_group == g}
            add_scope_delta(
                "matched_group",
                g,
                urls,
                metric,
                control_delta=control_deltas_by_metric.get(metric),
            )

    # Time series (mean by date/period/metric/role)
    bucket: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for o in inp.observations:
        page = pages_by_url.get(o.page_url)
        role = page.page_role if page else "unknown"
        bucket[(o.observed_at, o.period, o.metric_code, role)].append(o.value)
    time_series = [
        TimeSeriesPoint(
            observed_at=k[0],
            period=k[1],
            metric_code=k[2],
            scope_type="page_role",
            scope_id=k[3],
            value=float(mean(vals)),
        )
        for k, vals in sorted(bucket.items())
    ]

    # Causality per test variant × metric
    assessments: list[CausalityAssessmentResult] = []
    test_variant_codes = sorted(
        {
            p.variant_code
            for p in inp.pages
            if p.page_role == "test" and p.variant_code
        }
        or {v.variant_code for v in inp.variants if not v.is_baseline}
    )
    if not test_variant_codes:
        test_variant_codes = sorted(
            v.variant_code for v in inp.variants if not v.is_baseline
        ) or ["B"]

    for metric in metrics_present:
        control_d = control_deltas_by_metric.get(metric)
        for vc in test_variant_codes:
            variant_delta = next(
                (
                    d
                    for d in deltas
                    if d.scope_type == "variant"
                    and d.scope_id == vc
                    and d.metric_code == metric
                ),
                None,
            )
            if variant_delta is None:
                # Fall back to test pool
                variant_delta = next(
                    (
                        d
                        for d in deltas
                        if d.scope_type == "test_pool" and d.metric_code == metric
                    ),
                    None,
                )
            if variant_delta is None:
                continue
            assessments.append(
                classify_causality(
                    metric_code=metric,
                    variant_code=vc,
                    test_delta=variant_delta.absolute_delta,
                    control_delta=control_d,
                    control_adjusted_delta=variant_delta.control_adjusted_delta,
                    design_features=design,
                    n_pre=variant_delta.observation_count_pre,
                    n_post=variant_delta.observation_count_post,
                    known_confounds=inp.known_confounds,
                    concurrent_changes=inp.concurrent_changes,
                )
            )

    # Overall level = weakest assessment (most cautious), or correlation if none
    if assessments:
        rank = {lvl: i for i, lvl in enumerate(CAUSALITY_LEVELS)}
        overall = min(assessments, key=lambda a: rank[a.causality_level]).causality_level
        # Actually for "overall" we want the strongest design-supported level that still
        # respects warning — use max design strength but keep auto-reject. Product ask:
        # distinguish levels; overall should reflect best-supported careful claim ceiling.
        overall = max(assessments, key=lambda a: rank[a.causality_level]).causality_level
    else:
        overall = "correlation"

    # Always ensure every assessment rejects auto-causal conclusion
    assert all(a.auto_causal_conclusion_rejected for a in assessments)

    lifts = [
        d
        for d in deltas
        if d.scope_type in ("variant", "test_pool") and d.absolute_delta != 0
    ]
    summary = (
        f"GEO Lab analysed {len(inp.pages)} page(s), {len(metrics_present)} metric(s), "
        f"{len(inp.observations)} observation(s). Design: {', '.join(design)}. "
        f"Overall causality ceiling: {overall.replace('_', ' ')}. "
        f"{len(lifts)} non-zero test/variant delta(s). "
        f"{CAUSALITY_WARNING[:120]}…"
    )

    return ExperimentAnalysisResult(
        deltas=deltas,
        causality_assessments=assessments,
        time_series=time_series,
        overall_causality_level=overall,
        overall_summary=summary,
        causality_warning=CAUSALITY_WARNING,
        design_features=design,
    )
