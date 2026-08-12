"""Content Lab scoring — opportunities, Information Gain, Moat, Citability."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.content_lab import (
    CITABILITY_COMPONENTS,
    CITABILITY_DISCLAIMER,
    INFO_GAIN_PENALTIES,
    INFO_GAIN_REWARDS,
    MOAT_FORMAT_PRIORS,
    OPPORTUNITY_DIMENSIONS,
)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


@dataclass
class ProposalInput:
    title: str
    slug: str
    content_format: str = "article"
    angle: str | None = None
    target_url: str | None = None
    # Opportunity inputs 0–1 (optional; defaults derived from format/signals)
    seo_opportunity: float | None = None
    aeo_opportunity: float | None = None
    geo_opportunity: float | None = None
    ai_citation_opportunity: float | None = None
    business_value: float | None = None
    audience_relevance: float | None = None
    competitor_gap: float | None = None
    originality_opportunity: float | None = None
    topical_authority_impact: float | None = None
    conversion_potential: float | None = None
    backlink_potential: float | None = None
    entity_impact: float | None = None
    effort: float | None = None  # 0–1 where 1 = high effort
    time_sensitivity: float | None = None
    # Information gain signal flags / strengths 0–1
    info_gain_penalties: dict[str, float] = field(default_factory=dict)
    info_gain_rewards: dict[str, float] = field(default_factory=dict)
    # Citability component inputs 0–1
    citability_signals: dict[str, float] = field(default_factory=dict)
    # Moat overrides
    moat_override: float | None = None  # 0–100
    outline_text: str | None = None


@dataclass(slots=True)
class InfoGainSignalResult:
    signal_code: str
    polarity: str
    strength: float
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CitabilityComponentResult:
    component_code: str
    score: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProposalScore:
    title: str
    slug: str
    content_format: str
    angle: str | None
    target_url: str | None
    lab_priority_score: float
    opportunities: dict[str, float]  # 0–100 including effort/time_sensitivity
    information_gain_score: float
    content_moat_score: float
    generative_citability_score: float
    info_gain_signals: list[InfoGainSignalResult]
    citability_components: list[CitabilityComponentResult]
    moat_rationale: str
    recommendation_summary: str
    citability_disclaimer: str = CITABILITY_DISCLAIMER
    citability_is_proprietary_estimate: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_OPPORTUNITY_WEIGHTS: dict[str, float] = {
    "seo_opportunity": 0.08,
    "aeo_opportunity": 0.07,
    "geo_opportunity": 0.07,
    "ai_citation_opportunity": 0.09,
    "business_value": 0.09,
    "audience_relevance": 0.07,
    "competitor_gap": 0.07,
    "information_gain": 0.10,
    "originality_opportunity": 0.06,
    "topical_authority_impact": 0.06,
    "conversion_potential": 0.06,
    "backlink_potential": 0.05,
    "entity_impact": 0.05,
    "effort": 0.04,  # inverted: low effort boosts priority
    "time_sensitivity": 0.04,
}

CITABILITY_WEIGHTS: dict[str, float] = {
    "specificity": 0.12,
    "evidence": 0.12,
    "direct_answers": 0.12,
    "original_information": 0.12,
    "entity_clarity": 0.08,
    "source_attribution": 0.08,
    "freshness": 0.08,
    "structured_information": 0.08,
    "tables": 0.06,
    "definitions": 0.07,
    "comparisons": 0.07,
}


def _infer_format_priors(content_format: str) -> dict[str, float]:
    fmt = content_format.lower().strip().replace(" ", "_").replace("-", "_")
    priors = {
        "seo_opportunity": 0.55,
        "aeo_opportunity": 0.45,
        "geo_opportunity": 0.45,
        "ai_citation_opportunity": 0.4,
        "business_value": 0.5,
        "audience_relevance": 0.55,
        "competitor_gap": 0.4,
        "originality_opportunity": 0.35,
        "topical_authority_impact": 0.45,
        "conversion_potential": 0.4,
        "backlink_potential": 0.35,
        "entity_impact": 0.4,
        "effort": 0.45,
        "time_sensitivity": 0.35,
    }
    if fmt in {"generic_listicle", "listicle"}:
        priors.update(
            {
                "seo_opportunity": 0.6,
                "originality_opportunity": 0.2,
                "ai_citation_opportunity": 0.25,
                "effort": 0.25,
                "backlink_potential": 0.25,
            }
        )
    elif fmt in {"expert_interview", "interview"}:
        priors.update(
            {
                "aeo_opportunity": 0.65,
                "originality_opportunity": 0.7,
                "ai_citation_opportunity": 0.6,
                "entity_impact": 0.7,
                "effort": 0.55,
            }
        )
    elif fmt in {"original_dataset", "dataset"}:
        priors.update(
            {
                "geo_opportunity": 0.75,
                "ai_citation_opportunity": 0.8,
                "originality_opportunity": 0.9,
                "backlink_potential": 0.85,
                "effort": 0.75,
            }
        )
    elif fmt in {"proprietary_benchmark_study", "benchmark", "benchmark_study"}:
        priors.update(
            {
                "geo_opportunity": 0.85,
                "ai_citation_opportunity": 0.88,
                "originality_opportunity": 0.95,
                "backlink_potential": 0.9,
                "business_value": 0.8,
                "effort": 0.85,
            }
        )
    return priors


def _auto_detect_info_gain_from_text(
    text: str | None, content_format: str
) -> tuple[dict[str, float], dict[str, float]]:
    """Lightweight heuristic detection of penalty/reward cues in outline/angle."""
    penalties: dict[str, float] = {}
    rewards: dict[str, float] = {}
    blob = f"{text or ''} {content_format}".lower()

    penalty_patterns = {
        "generic_duplication": r"\b(ultimate guide|everything you need|101|basics)\b",
        "near_identical_competitor_coverage": r"\b(like competitors?|same as|me too)\b",
        "common_definitions": r"\b(what is|definition of|simply put)\b",
        "repeated_statistics": r"\b(widely cited|same stat|industry average only)\b",
        "commodity_advice": r"\b(tips and tricks|best practices only|top \d+ tips)\b",
    }
    reward_patterns = {
        "original_data": r"\b(survey of|our data|n=\d+|sample of)\b",
        "original_experiment": r"\b(experiment|we tested|a/?b test)\b",
        "new_comparison": r"\b(vs\.?|versus|head[- ]to[- ]head|benchmark)\b",
        "expert_opinion": r"\b(interview|cites? expert|according to our)\b",
        "first_party_insight": r"\b(first[- ]party|from our customers|internal)\b",
        "unique_framework": r"\b(framework|model we|playbook)\b",
        "new_synthesis": r"\b(synthesis|we combined|cross[- ]analysis)\b",
        "fresh_statistics": r"\b(20\d{2} data|this quarter|newly released)\b",
        "novel_example": r"\b(case study|worked example|walkthrough)\b",
    }
    for code, pat in penalty_patterns.items():
        if re.search(pat, blob):
            penalties[code] = 0.55
    for code, pat in reward_patterns.items():
        if re.search(pat, blob):
            rewards[code] = 0.65

    fmt = content_format.lower().replace(" ", "_").replace("-", "_")
    if fmt in {"generic_listicle", "listicle"}:
        penalties.setdefault("commodity_advice", 0.7)
        penalties.setdefault("generic_duplication", 0.6)
    if fmt in {"original_dataset", "dataset"}:
        rewards.setdefault("original_data", 0.9)
    if fmt in {"proprietary_benchmark_study", "benchmark", "benchmark_study"}:
        rewards.setdefault("original_data", 0.85)
        rewards.setdefault("new_comparison", 0.8)
        rewards.setdefault("fresh_statistics", 0.75)
    if fmt in {"expert_interview", "interview"}:
        rewards.setdefault("expert_opinion", 0.8)
        rewards.setdefault("first_party_insight", 0.5)

    return penalties, rewards


def compute_information_gain(
    *,
    penalties: dict[str, float],
    rewards: dict[str, float],
) -> tuple[float, list[InfoGainSignalResult]]:
    """Information Gain Score 0–100: whether content adds beyond what exists."""
    signals: list[InfoGainSignalResult] = []
    penalty_mass = 0.0
    for code in INFO_GAIN_PENALTIES:
        strength = _clamp01(penalties.get(code, 0.0))
        if strength <= 0:
            continue
        penalty_mass += strength
        signals.append(
            InfoGainSignalResult(
                signal_code=code,
                polarity="penalty",
                strength=round(strength, 4),
                evidence=f"Detected risk of {code.replace('_', ' ')} (strength {strength:.2f}).",
            )
        )
    reward_mass = 0.0
    for code in INFO_GAIN_REWARDS:
        strength = _clamp01(rewards.get(code, 0.0))
        if strength <= 0:
            continue
        reward_mass += strength
        signals.append(
            InfoGainSignalResult(
                signal_code=code,
                polarity="reward",
                strength=round(strength, 4),
                evidence=f"Detected {code.replace('_', ' ')} (strength {strength:.2f}).",
            )
        )

    # Base 45; rewards lift, penalties cut. Caps keep score in range.
    raw = 0.45 + 0.12 * reward_mass - 0.14 * penalty_mass
    score = _clamp100(100.0 * _clamp01(raw))
    if not signals:
        signals.append(
            InfoGainSignalResult(
                signal_code="insufficient_signals",
                polarity="penalty",
                strength=0.3,
                evidence="Limited originality signals observed; score near neutral prior.",
            )
        )
    return round(score, 2), signals


def compute_content_moat(
    *,
    content_format: str,
    information_gain_score: float,
    originality_opportunity: float,
    moat_override: float | None = None,
) -> tuple[float, str]:
    """Content Moat Score 0–100: difficulty for competitors to replicate."""
    if moat_override is not None:
        score = _clamp100(moat_override)
        return round(score, 2), f"Moat override provided ({score:.0f}/100)."

    fmt = content_format.lower().strip().replace(" ", "_").replace("-", "_")
    # Normalise aliases
    alias = {
        "listicle": "generic_listicle",
        "interview": "expert_interview",
        "dataset": "original_dataset",
        "benchmark": "proprietary_benchmark_study",
        "benchmark_study": "proprietary_benchmark_study",
    }
    fmt = alias.get(fmt, fmt)
    prior = MOAT_FORMAT_PRIORS.get(fmt)
    if prior is None:
        # Blend originality + info gain for unknown formats
        prior = int(round(20 + 60 * _clamp01(originality_opportunity) + 0.15 * information_gain_score))
        prior = int(_clamp100(prior))

    # Nudge by information gain relative to format prior
    nudge = (information_gain_score - 50.0) * 0.12
    score = _clamp100(prior + nudge)
    examples = ", ".join(f"{k.replace('_', ' ')}={v}" for k, v in MOAT_FORMAT_PRIORS.items())
    rationale = (
        f"Format prior for '{fmt}' is {prior}/100 "
        f"(reference: {examples}). "
        f"Adjusted by Information Gain ({information_gain_score:.0f}/100) → {score:.0f}/100. "
        "Higher moat means harder for competitors to replicate."
    )
    return round(score, 2), rationale


def compute_generative_citability(
    signals: dict[str, float],
    *,
    information_gain_score: float,
) -> tuple[float, list[CitabilityComponentResult]]:
    """Peacock proprietary estimate — not a guaranteed third-party ranking factor."""
    components: list[CitabilityComponentResult] = []
    # Soft defaults from info gain for missing signals
    ig = information_gain_score / 100.0
    defaults = {
        "specificity": 0.45,
        "evidence": 0.4 + 0.3 * ig,
        "direct_answers": 0.45,
        "original_information": ig,
        "entity_clarity": 0.45,
        "source_attribution": 0.4,
        "freshness": 0.45,
        "structured_information": 0.4,
        "tables": 0.3,
        "definitions": 0.4,
        "comparisons": 0.35,
    }
    weighted = 0.0
    for code in CITABILITY_COMPONENTS:
        val = signals.get(code)
        if val is None:
            val = defaults[code]
        val = _clamp01(val)
        weighted += CITABILITY_WEIGHTS[code] * val
        components.append(
            CitabilityComponentResult(
                component_code=code,
                score=round(100.0 * val, 2),
                explanation=(
                    f"{code.replace('_', ' ').title()} contributes to Peacock's proprietary "
                    f"Generative Citability estimate at {100*val:.0f}/100."
                ),
            )
        )
    score = _clamp100(100.0 * weighted)
    return round(score, 2), components


def evaluate_proposal(proposal: ProposalInput) -> ProposalScore:
    """Full Content Lab evaluation for one proposed piece of content."""
    priors = _infer_format_priors(proposal.content_format)
    auto_pen, auto_rew = _auto_detect_info_gain_from_text(
        f"{proposal.angle or ''} {proposal.outline_text or ''} {proposal.title}",
        proposal.content_format,
    )
    penalties = {**auto_pen, **{k: _clamp01(v) for k, v in proposal.info_gain_penalties.items()}}
    rewards = {**auto_rew, **{k: _clamp01(v) for k, v in proposal.info_gain_rewards.items()}}

    info_gain, ig_signals = compute_information_gain(penalties=penalties, rewards=rewards)

    def opp(name: str, explicit: float | None) -> float:
        if explicit is not None:
            return _clamp100(100.0 * _clamp01(explicit))
        if name == "information_gain":
            return info_gain
        return _clamp100(100.0 * priors.get(name, 0.45))

    opportunities = {
        "seo_opportunity": opp("seo_opportunity", proposal.seo_opportunity),
        "aeo_opportunity": opp("aeo_opportunity", proposal.aeo_opportunity),
        "geo_opportunity": opp("geo_opportunity", proposal.geo_opportunity),
        "ai_citation_opportunity": opp("ai_citation_opportunity", proposal.ai_citation_opportunity),
        "business_value": opp("business_value", proposal.business_value),
        "audience_relevance": opp("audience_relevance", proposal.audience_relevance),
        "competitor_gap": opp("competitor_gap", proposal.competitor_gap),
        "information_gain": info_gain,
        "originality_opportunity": opp("originality_opportunity", proposal.originality_opportunity),
        "topical_authority_impact": opp(
            "topical_authority_impact", proposal.topical_authority_impact
        ),
        "conversion_potential": opp("conversion_potential", proposal.conversion_potential),
        "backlink_potential": opp("backlink_potential", proposal.backlink_potential),
        "entity_impact": opp("entity_impact", proposal.entity_impact),
        "effort": opp("effort", proposal.effort),
        "time_sensitivity": opp("time_sensitivity", proposal.time_sensitivity),
    }
    assert set(opportunities) == set(OPPORTUNITY_DIMENSIONS)

    originality01 = opportunities["originality_opportunity"] / 100.0
    moat, moat_rationale = compute_content_moat(
        content_format=proposal.content_format,
        information_gain_score=info_gain,
        originality_opportunity=originality01,
        moat_override=proposal.moat_override,
    )

    citability, cit_components = compute_generative_citability(
        proposal.citability_signals,
        information_gain_score=info_gain,
    )

    # Priority: weighted opportunities; effort inverted (high effort lowers priority)
    w = DEFAULT_OPPORTUNITY_WEIGHTS
    priority = 0.0
    for key, weight in w.items():
        val = opportunities[key] / 100.0
        if key == "effort":
            val = 1.0 - val
        priority += weight * val
    # Blend in moat + citability lightly
    priority = _clamp100(100.0 * (0.82 * priority + 0.1 * (moat / 100.0) + 0.08 * (citability / 100.0)))

    summary = (
        f"Lab priority {priority:.0f}/100. Information Gain {info_gain:.0f}/100, "
        f"Content Moat {moat:.0f}/100, Generative Citability {citability:.0f}/100 "
        f"(Peacock proprietary estimate — not a guaranteed third-party ranking factor)."
    )

    return ProposalScore(
        title=proposal.title,
        slug=proposal.slug,
        content_format=proposal.content_format,
        angle=proposal.angle,
        target_url=proposal.target_url,
        lab_priority_score=round(priority, 2),
        opportunities={k: round(v, 2) for k, v in opportunities.items()},
        information_gain_score=info_gain,
        content_moat_score=moat,
        generative_citability_score=citability,
        info_gain_signals=ig_signals,
        citability_components=cit_components,
        moat_rationale=moat_rationale,
        recommendation_summary=summary,
    )


def evaluate_proposals(proposals: list[ProposalInput]) -> list[ProposalScore]:
    scores = [evaluate_proposal(p) for p in proposals]
    scores.sort(key=lambda s: s.lab_priority_score, reverse=True)
    return scores


def signals_json(signals: list[InfoGainSignalResult]) -> str:
    return json.dumps([s.to_dict() for s in signals], sort_keys=True)
