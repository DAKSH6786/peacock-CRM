"""Research Mode analysis — controlled study pipeline with uncertainty."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from db_models.research_mode import (
    CAUSALITY_WARNING,
    FINDING_VERDICTS,
    LABORATORY_POSITIONING,
    METHODOLOGY_NOTE,
    OBSERVATION_ARMS,
    PAGE_ROLES,
    RESEARCH_METRIC_LABELS,
    RESEARCH_METRICS,
    STUDY_PHASES,
    UNCERTAINTY_BANDS,
)


@dataclass
class PageSpec:
    url: str
    page_role: str = "treatment"
    label: str | None = None

    def validate(self) -> None:
        if self.page_role not in PAGE_ROLES:
            raise ValueError(f"Unsupported page_role: {self.page_role}")
        if not self.url.strip():
            raise ValueError("page url is required")


@dataclass
class PromptSpec:
    prompt_text: str
    prompt_cluster: str | None = None

    def validate(self) -> None:
        if not self.prompt_text.strip():
            raise ValueError("prompt_text is required")


@dataclass
class ObservationSpec:
    arm: str
    round_index: int
    page_url: str
    page_role: str
    prompt_text: str
    value: float
    observed_at: datetime | None = None

    def validate(self) -> None:
        if self.arm not in OBSERVATION_ARMS:
            raise ValueError(f"Unsupported arm: {self.arm}")
        if self.page_role not in PAGE_ROLES:
            raise ValueError(f"Unsupported page_role: {self.page_role}")


@dataclass
class ResearchStudySpec:
    client_brand: str
    research_question: str
    hypothesis: str
    metric_key: str
    treatment_description: str
    pages: list[PageSpec] = field(default_factory=list)
    prompts: list[PromptSpec] = field(default_factory=list)
    observations: list[ObservationSpec] = field(default_factory=list)
    observation_rounds: int = 3
    analysed_at: datetime | None = None


@dataclass(slots=True)
class PageResult:
    url: str
    page_role: str
    label: str | None
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PromptResult:
    prompt_text: str
    prompt_cluster: str | None
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ObservationResult:
    arm: str
    round_index: int
    page_url: str
    page_role: str
    prompt_text: str
    metric_key: str
    value: float
    observed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["observed_at"] = self.observed_at.isoformat()
        return d


@dataclass(slots=True)
class FindingResult:
    finding_index: int
    verdict: str
    claim: str
    evidence: str
    uncertainty_band: str
    uncertainty_rationale: str
    auto_causal_conclusion_rejected: bool
    next_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ResearchStudyResult:
    client_brand: str
    research_question: str
    hypothesis: str
    metric_key: str
    metric_label: str
    treatment_description: str
    completed_phases: list[str]
    pages: list[PageResult]
    prompts: list[PromptResult]
    observations: list[ObservationResult]
    findings: list[FindingResult]
    baseline_mean: float | None
    treatment_mean: float | None
    absolute_delta: float | None
    relative_delta_pct: float | None
    control_adjusted_delta: float | None
    uncertainty_band: str
    uncertainty_score: float
    finding_verdict: str
    finding_summary: str
    observation_rounds: int
    pages_count: int
    prompts_count: int
    laboratory_positioning: str
    causality_warning: str
    methodology_note: str
    analysed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "research_question": self.research_question,
            "hypothesis": self.hypothesis,
            "metric_key": self.metric_key,
            "metric_label": self.metric_label,
            "treatment_description": self.treatment_description,
            "completed_phases": self.completed_phases,
            "pages": [p.to_dict() for p in self.pages],
            "prompts": [p.to_dict() for p in self.prompts],
            "observations": [o.to_dict() for o in self.observations],
            "findings": [f.to_dict() for f in self.findings],
            "baseline_mean": self.baseline_mean,
            "treatment_mean": self.treatment_mean,
            "absolute_delta": self.absolute_delta,
            "relative_delta_pct": self.relative_delta_pct,
            "control_adjusted_delta": self.control_adjusted_delta,
            "uncertainty_band": self.uncertainty_band,
            "uncertainty_score": self.uncertainty_score,
            "finding_verdict": self.finding_verdict,
            "finding_summary": self.finding_summary,
            "observation_rounds": self.observation_rounds,
            "pages_count": self.pages_count,
            "prompts_count": self.prompts_count,
            "laboratory_positioning": self.laboratory_positioning,
            "causality_warning": self.causality_warning,
            "methodology_note": self.methodology_note,
            "analysed_at": self.analysed_at.isoformat(),
        }


def catalog() -> dict[str, Any]:
    return {
        "study_phases": list(STUDY_PHASES),
        "observation_arms": list(OBSERVATION_ARMS),
        "page_roles": list(PAGE_ROLES),
        "research_metrics": list(RESEARCH_METRICS),
        "research_metric_labels": dict(RESEARCH_METRIC_LABELS),
        "finding_verdicts": list(FINDING_VERDICTS),
        "uncertainty_bands": list(UNCERTAINTY_BANDS),
        "laboratory_positioning": LABORATORY_POSITIONING,
        "causality_warning": CAUSALITY_WARNING,
        "methodology_note": METHODOLOGY_NOTE,
        "example_research_question": (
            "Does adding proprietary statistics increase AI citation probability?"
        ),
        "product_note": (
            "Peacock Research Mode is the experimental method in the product — "
            "a search intelligence laboratory for controlled analyses, not a "
            "generic SEO checklist."
        ),
    }


def demo_pages() -> list[PageSpec]:
    return [
        PageSpec("https://example.com/guides/benchmarks", "treatment", "Benchmarks hub"),
        PageSpec("https://example.com/guides/roi", "treatment", "ROI guide"),
        PageSpec("https://example.com/blog/industry-overview", "control", "Control overview"),
    ]


def demo_prompts() -> list[PromptSpec]:
    return [
        PromptSpec("What are the best enterprise CRM benchmarks?", "commercial"),
        PromptSpec("Which CRM vendors publish original statistics?", "evidence"),
        PromptSpec("Compare CRM platforms with proprietary data", "comparison"),
    ]


def demo_observations(
    *,
    pages: list[PageSpec],
    prompts: list[PromptSpec],
    rounds: int,
    metric_key: str,
    analysed_at: datetime,
) -> list[ObservationSpec]:
    """Synthetic baseline/treatment series for the example research question."""
    obs: list[ObservationSpec] = []
    for r in range(rounds):
        for page in pages:
            for prompt in prompts:
                # Baseline: modest citation probability
                base = 0.22 + (0.01 * r) + (0.02 if page.page_role == "control" else 0.0)
                # Treatment: lift on treatment pages only
                treat = base + (0.11 if page.page_role == "treatment" else 0.015)
                # Small round noise
                base += 0.005 * (r % 2)
                treat += 0.004 * ((r + 1) % 2)
                t0 = analysed_at - timedelta(days=14 - r)
                t1 = analysed_at - timedelta(days=3 - r)
                obs.append(
                    ObservationSpec(
                        arm="baseline",
                        round_index=r,
                        page_url=page.url,
                        page_role=page.page_role,
                        prompt_text=prompt.prompt_text,
                        value=round(base, 4),
                        observed_at=t0,
                    )
                )
                obs.append(
                    ObservationSpec(
                        arm="treatment",
                        round_index=r,
                        page_url=page.url,
                        page_role=page.page_role,
                        prompt_text=prompt.prompt_text,
                        value=round(min(0.95, treat), 4),
                        observed_at=t1,
                    )
                )
    _ = metric_key
    return obs


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(statistics.fmean(values), 4)


def _stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


def _uncertainty(
    *,
    rounds: int,
    n_obs: int,
    has_control: bool,
    baseline_vals: list[float],
    treatment_vals: list[float],
    absolute_delta: float | None,
) -> tuple[str, float, str]:
    """Return (band, score 0-1 higher=more uncertain, rationale)."""
    score = 0.35
    notes: list[str] = []
    if rounds < 3:
        score += 0.2
        notes.append("fewer than 3 observation rounds")
    if n_obs < 12:
        score += 0.15
        notes.append("small observation count")
    if not has_control:
        score += 0.2
        notes.append("no control pages")
    if baseline_vals and treatment_vals:
        pooled = _stdev(baseline_vals + treatment_vals)
        if absolute_delta is not None and pooled > 0 and abs(absolute_delta) < 1.2 * pooled:
            score += 0.15
            notes.append("delta near noise scale")
    score = max(0.1, min(0.95, score))
    if score < 0.35:
        band = "low"
    elif score < 0.55:
        band = "moderate"
    elif score < 0.75:
        band = "high"
    else:
        band = "very_high"
    rationale = (
        f"Uncertainty band={band} (score {score:.2f})"
        + (f" due to: {', '.join(notes)}." if notes else " with adequate design coverage.")
        + " Not a p-value; directional laboratory uncertainty."
    )
    return band, round(score, 3), rationale


def _verdict(
    *,
    absolute_delta: float | None,
    control_adjusted: float | None,
    uncertainty_band: str,
) -> str:
    if absolute_delta is None:
        return "needs_more_data"
    if uncertainty_band in ("high", "very_high") and abs(absolute_delta) < 0.08:
        return "inconclusive"
    delta = control_adjusted if control_adjusted is not None else absolute_delta
    if delta >= 0.05:
        return "supports_hypothesis"
    if delta <= -0.05:
        return "does_not_support_hypothesis"
    return "inconclusive"


def analyse_research_study(spec: ResearchStudySpec) -> ResearchStudyResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")
    question = (spec.research_question or "").strip()
    hypothesis = (spec.hypothesis or "").strip()
    treatment = (spec.treatment_description or "").strip()
    if not question:
        raise ValueError("research_question is required")
    if not hypothesis:
        raise ValueError("hypothesis is required")
    if not treatment:
        raise ValueError("treatment_description is required")

    metric_key = (spec.metric_key or "").strip()
    if metric_key not in RESEARCH_METRICS:
        raise ValueError(f"Unsupported metric_key: {metric_key}")
    metric_label = RESEARCH_METRIC_LABELS[metric_key]

    for p in spec.pages:
        p.validate()
    for p in spec.prompts:
        p.validate()
    for o in spec.observations:
        o.validate()

    pages_in = list(spec.pages) or demo_pages()
    prompts_in = list(spec.prompts) or demo_prompts()
    rounds = max(1, int(spec.observation_rounds or 3))
    analysed_at = spec.analysed_at or datetime.now(tz=UTC)

    obs_in = list(spec.observations)
    if not obs_in:
        obs_in = demo_observations(
            pages=pages_in,
            prompts=prompts_in,
            rounds=rounds,
            metric_key=metric_key,
            analysed_at=analysed_at,
        )

    pages = [
        PageResult(url=p.url, page_role=p.page_role, label=p.label, rank_order=i)
        for i, p in enumerate(pages_in)
    ]
    prompts = [
        PromptResult(
            prompt_text=p.prompt_text,
            prompt_cluster=p.prompt_cluster,
            rank_order=i,
        )
        for i, p in enumerate(prompts_in)
    ]
    observations = [
        ObservationResult(
            arm=o.arm,
            round_index=o.round_index,
            page_url=o.page_url,
            page_role=o.page_role,
            prompt_text=o.prompt_text,
            metric_key=metric_key,
            value=float(o.value),
            observed_at=o.observed_at or analysed_at,
        )
        for o in obs_in
    ]

    # Baseline / treatment on treatment pages
    treat_pages = {p.url for p in pages if p.page_role == "treatment"}
    control_pages = {p.url for p in pages if p.page_role == "control"}
    base_t = [
        o.value
        for o in observations
        if o.arm == "baseline" and o.page_url in treat_pages
    ]
    treat_t = [
        o.value
        for o in observations
        if o.arm == "treatment" and o.page_url in treat_pages
    ]
    base_c = [
        o.value
        for o in observations
        if o.arm == "baseline" and o.page_url in control_pages
    ]
    treat_c = [
        o.value
        for o in observations
        if o.arm == "treatment" and o.page_url in control_pages
    ]

    baseline_mean = _mean(base_t)
    treatment_mean = _mean(treat_t)
    absolute_delta = (
        round(treatment_mean - baseline_mean, 4)
        if baseline_mean is not None and treatment_mean is not None
        else None
    )
    relative_delta_pct = (
        round(100.0 * absolute_delta / baseline_mean, 2)
        if absolute_delta is not None and baseline_mean not in (None, 0)
        else None
    )
    control_delta = None
    if base_c and treat_c and absolute_delta is not None:
        c_delta = statistics.fmean(treat_c) - statistics.fmean(base_c)
        control_delta = round(absolute_delta - c_delta, 4)

    max_round = max((o.round_index for o in observations), default=rounds - 1) + 1
    band, u_score, u_rationale = _uncertainty(
        rounds=max_round,
        n_obs=len(observations),
        has_control=bool(control_pages),
        baseline_vals=base_t,
        treatment_vals=treat_t,
        absolute_delta=absolute_delta,
    )
    verdict = _verdict(
        absolute_delta=absolute_delta,
        control_adjusted=control_delta,
        uncertainty_band=band,
    )

    delta_txt = (
        f"{absolute_delta:+.4f}" if absolute_delta is not None else "n/a"
    )
    adj_txt = (
        f"{control_delta:+.4f}" if control_delta is not None else "n/a"
    )
    finding_summary = (
        f"Study on '{question}': treatment pages moved {metric_label} by {delta_txt} "
        f"(control-adjusted {adj_txt}). Verdict: {verdict.replace('_', ' ')} "
        f"with {band} uncertainty. Auto causal slogans rejected."
    )

    findings = [
        FindingResult(
            finding_index=0,
            verdict=verdict,
            claim=(
                f"Observed {metric_label} change on treatment pages after: {treatment}."
            ),
            evidence=(
                f"Baseline mean={baseline_mean}, treatment mean={treatment_mean}, "
                f"absolute Δ={delta_txt}, control-adjusted Δ={adj_txt}, "
                f"rounds={max_round}, observations={len(observations)}, "
                f"pages={len(pages)}, prompts={len(prompts)}."
            ),
            uncertainty_band=band,
            uncertainty_rationale=u_rationale,
            auto_causal_conclusion_rejected=True,
            next_step=(
                "Repeat observations across more prompt clusters and holdout pages "
                "before operationalising the treatment broadly."
                if verdict in ("supports_hypothesis", "inconclusive")
                else "Revisit treatment design or metric sensitivity; gather more rounds."
            ),
        ),
        FindingResult(
            finding_index=1,
            verdict="needs_more_data" if band in ("high", "very_high") else verdict,
            claim=CAUSALITY_WARNING,
            evidence=u_rationale,
            uncertainty_band=band,
            uncertainty_rationale=u_rationale,
            auto_causal_conclusion_rejected=True,
            next_step=(
                "Keep Research Mode in laboratory posture: publish findings with "
                "uncertainty, not marketing certainty."
            ),
        ),
    ]

    return ResearchStudyResult(
        client_brand=brand,
        research_question=question,
        hypothesis=hypothesis,
        metric_key=metric_key,
        metric_label=metric_label,
        treatment_description=treatment,
        completed_phases=list(STUDY_PHASES),
        pages=pages,
        prompts=prompts,
        observations=sorted(
            observations, key=lambda o: (o.arm, o.round_index, o.page_url, o.prompt_text)
        ),
        findings=findings,
        baseline_mean=baseline_mean,
        treatment_mean=treatment_mean,
        absolute_delta=absolute_delta,
        relative_delta_pct=relative_delta_pct,
        control_adjusted_delta=control_delta,
        uncertainty_band=band,
        uncertainty_score=u_score,
        finding_verdict=verdict,
        finding_summary=finding_summary,
        observation_rounds=max_round,
        pages_count=len(pages),
        prompts_count=len(prompts),
        laboratory_positioning=LABORATORY_POSITIONING,
        causality_warning=CAUSALITY_WARNING,
        methodology_note=METHODOLOGY_NOTE,
        analysed_at=analysed_at,
    )
