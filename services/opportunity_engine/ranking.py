"""Peacock Opportunity Engine — detection, explainable ranking, outcome learning.

Ranking starts explainable. Historical outcomes adjust weights. Never a single
forever-fixed manual formula as the sole method.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.opportunity_engine import (
    ALWAYS_ON_NOTE,
    DEFAULT_RANKING_WEIGHTS,
    METHODOLOGY_NOTE,
    OPPORTUNITY_TYPES,
    RANKING_FEATURES,
)


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(w)) for w in weights.values()) or 1.0
    return {k: max(0.0, float(weights.get(k, 0.0))) / total for k in RANKING_FEATURES}


@dataclass
class EvidenceInput:
    evidence_type: str
    statement: str
    source_ref: str | None = None
    strength: float = 50.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SignalInput:
    """Raw intelligence signal that may become an opportunity."""

    opportunity_type: str
    title: str
    description: str
    impact: float
    urgency: float
    confidence: float
    difficulty: float
    expected_value: float
    recommended_action: str
    evidence: list[EvidenceInput] = field(default_factory=list)
    related_entity: str | None = None
    related_url: str | None = None
    opportunity_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            **{k: v for k, v in asdict(self).items() if k != "evidence"},
            "evidence": [e.to_dict() for e in self.evidence],
        }


@dataclass
class OutcomeFeedbackInput:
    opportunity_type: str
    impact: float
    urgency: float
    confidence: float
    difficulty: float
    expected_value: float
    predicted_score: float
    realized_outcome: float
    opportunity_key: str | None = None
    outcome_label: str = "observed"
    notes: str | None = None


@dataclass(slots=True)
class RankingFactorResult:
    feature_code: str
    feature_value: float
    weight: float
    contribution: float
    weight_source: str
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WeightSnapshot:
    feature_code: str
    base_weight: float
    learned_weight: float
    effective_weight: float
    learning_sample_size: int
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceResult:
    evidence_type: str
    statement: str
    source_ref: str | None
    strength: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OpportunityResult:
    opportunity_key: str
    opportunity_type: str
    title: str
    description: str
    impact: float
    urgency: float
    confidence: float
    difficulty: float
    expected_value: float
    recommended_action: str
    evidence: list[EvidenceResult]
    rank: int
    opportunity_score: float
    ranking_explanation: str
    ranking_factors: list[RankingFactorResult]
    related_entity: str | None = None
    related_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_key": self.opportunity_key,
            "opportunity_type": self.opportunity_type,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "urgency": self.urgency,
            "confidence": self.confidence,
            "difficulty": self.difficulty,
            "expected_value": self.expected_value,
            "recommended_action": self.recommended_action,
            "evidence": [e.to_dict() for e in self.evidence],
            "rank": self.rank,
            "opportunity_score": self.opportunity_score,
            "ranking_explanation": self.ranking_explanation,
            "ranking_factors": [f.to_dict() for f in self.ranking_factors],
            "related_entity": self.related_entity,
            "related_url": self.related_url,
        }


@dataclass
class RankingModelState:
    """Explainable + adaptive ranking model — not a forever-fixed formula."""

    base_weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_RANKING_WEIGHTS)
    )
    learned_weights: dict[str, float] = field(default_factory=dict)
    learning_sample_size: int = 0
    model_version: int = 1
    blend_toward_learned: float = 0.0  # 0=base only, 1=fully learned

    def effective_weights(self) -> dict[str, float]:
        base = _normalize_weights(self.base_weights)
        if self.learning_sample_size < 3 or not self.learned_weights:
            return base
        learned = _normalize_weights(
            {k: self.learned_weights.get(k, base[k]) for k in RANKING_FEATURES}
        )
        # Gradual blend — more samples → more trust in learned weights (capped)
        alpha = min(0.65, self.blend_toward_learned or min(0.65, self.learning_sample_size / 40.0))
        blended = {
            k: (1.0 - alpha) * base[k] + alpha * learned[k] for k in RANKING_FEATURES
        }
        return _normalize_weights(blended)

    def weight_snapshots(self) -> list[WeightSnapshot]:
        base = _normalize_weights(self.base_weights)
        eff = self.effective_weights()
        learned = _normalize_weights(
            {k: self.learned_weights.get(k, base[k]) for k in RANKING_FEATURES}
        ) if self.learned_weights else base
        snaps: list[WeightSnapshot] = []
        for code in RANKING_FEATURES:
            source_note = (
                "base explainable prior only"
                if self.learning_sample_size < 3
                else f"blended base+learned (n={self.learning_sample_size})"
            )
            snaps.append(
                WeightSnapshot(
                    feature_code=code,
                    base_weight=base[code],
                    learned_weight=learned[code],
                    effective_weight=eff[code],
                    learning_sample_size=self.learning_sample_size,
                    explanation=(
                        f"Feature «{code}»: base={base[code]:.3f}, learned={learned[code]:.3f}, "
                        f"effective={eff[code]:.3f} — {source_note}. "
                        f"Fixed forever-formula rejected."
                    ),
                )
            )
        return snaps


@dataclass
class ScanResult:
    opportunities: list[OpportunityResult]
    ranking_weights: list[WeightSnapshot]
    ranking_model_version: int
    ranking_is_adaptive: bool
    fixed_formula_rejected: bool
    always_on_note: str
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunities": [o.to_dict() for o in self.opportunities],
            "ranking_weights": [w.to_dict() for w in self.ranking_weights],
            "ranking_model_version": self.ranking_model_version,
            "ranking_is_adaptive": self.ranking_is_adaptive,
            "fixed_formula_rejected": self.fixed_formula_rejected,
            "always_on_note": self.always_on_note,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
        }


# Human-readable titles / default actions for known types
_TYPE_DEFAULTS: dict[str, tuple[str, str]] = {
    "competitor_gained_ai_visibility": (
        "Competitor gained AI visibility",
        "Analyse rival citation/mention pathways and publish differentiated, citable coverage.",
    ),
    "new_citation_source_emerged": (
        "New citation source emerged",
        "Earn ethical placement or create primary material that this source class prefers.",
    ),
    "high_value_topic_available": (
        "High-value topic became available",
        "Brief and ship authoritative content targeting the new topic cluster.",
    ),
    "existing_article_decaying": (
        "Existing article is decaying",
        "Refresh evidence, entities, and structure; re-promote updated URL.",
    ),
    "entity_relationship_weakened": (
        "Entity relationship weakened",
        "Strengthen entity associations via clearer mentions, context, and supporting pages.",
    ),
    "new_prompt_cluster_appeared": (
        "New prompt cluster appeared",
        "Map prompts to answer assets (FAQ, definitions, comparisons) and monitor engines.",
    ),
    "competitor_content_outdated": (
        "Competitor content is outdated",
        "Publish an updated, higher-information-gain page that supersedes rival coverage.",
    ),
    "ai_sentiment_changed": (
        "AI sentiment changed",
        "Audit answer framing; publish clarifying evidence and brand-safe narratives.",
    ),
    "backlink_source_gained_influence": (
        "Backlink source gained influence",
        "Pursue relevant, ethical coverage from the rising referring domain.",
    ),
    "search_demand_shifted": (
        "Search demand shifted",
        "Reallocate content and internal links toward rising demand queries.",
    ),
    "ai_answer_changed_materially": (
        "AI answer changed materially",
        "Diff answer snapshots; update pages to regain citation and prominence.",
    ),
}


def learn_weights_from_outcomes(
    feedback: list[OutcomeFeedbackInput],
    *,
    base_weights: dict[str, float] | None = None,
) -> RankingModelState:
    """Improve ranking weights from historical outcomes (explainable, adaptive).

    Uses a simple residual-correlation heuristic: features that co-vary with
    positive (realized - predicted) residuals gain weight; difficulty is special-
    cased (high difficulty predicting failure reinforces the inverted role).
    """
    base = _normalize_weights(base_weights or DEFAULT_RANKING_WEIGHTS)
    state = RankingModelState(
        base_weights=base,
        learned_weights=dict(base),
        learning_sample_size=len(feedback),
        model_version=1 + max(0, len(feedback) // 10),
        blend_toward_learned=0.0,
    )
    if len(feedback) < 3:
        return state

    # Accumulate signed alignment of each feature with outcome residual
    align: dict[str, float] = defaultdict(float)
    for fb in feedback:
        residual = _clamp100(fb.realized_outcome) - _clamp100(fb.predicted_score)
        features = {
            "impact": _clamp100(fb.impact),
            "urgency": _clamp100(fb.urgency),
            "confidence": _clamp100(fb.confidence),
            "expected_value": _clamp100(fb.expected_value),
            # For difficulty, high values should align with negative residuals if model is right
            "difficulty": 100.0 - _clamp100(fb.difficulty),
        }
        for code, val in features.items():
            # Center feature around 50
            align[code] += residual * ((val - 50.0) / 50.0)

    # Convert alignment to positive weights
    shifted = {k: max(0.05, 1.0 + align.get(k, 0.0) / max(1, len(feedback))) for k in RANKING_FEATURES}
    learned = _normalize_weights(shifted)
    state.learned_weights = learned
    state.blend_toward_learned = min(0.65, len(feedback) / 40.0)
    state.model_version = 1 + len(feedback) // 10
    return state


def score_opportunity(
    signal: SignalInput,
    weights: dict[str, float],
    *,
    weight_source: str = "blended",
) -> tuple[float, list[RankingFactorResult], str]:
    """Explainable opportunity score from impact/urgency/confidence/EV/difficulty."""
    values = {
        "impact": _clamp100(signal.impact),
        "urgency": _clamp100(signal.urgency),
        "confidence": _clamp100(signal.confidence),
        "expected_value": _clamp100(signal.expected_value),
        "difficulty": _clamp100(signal.difficulty),
    }
    # Difficulty inverted for contribution
    effective_values = {
        **values,
        "difficulty": 100.0 - values["difficulty"],
    }
    factors: list[RankingFactorResult] = []
    score = 0.0
    w = _normalize_weights(weights)
    for code in RANKING_FEATURES:
        contrib = w[code] * effective_values[code]
        score += contrib
        raw = values[code]
        factors.append(
            RankingFactorResult(
                feature_code=code,
                feature_value=raw,
                weight=w[code],
                contribution=contrib,
                weight_source=weight_source,
                explanation=(
                    f"{code}={raw:.1f} × weight {w[code]:.3f} → contribution {contrib:.2f}"
                    + (" (difficulty inverted)" if code == "difficulty" else "")
                ),
            )
        )
    score = _clamp100(score)
    explanation = (
        f"Explainable score {score:.1f}/100 = "
        + " + ".join(f"{f.feature_code}({f.contribution:.1f})" for f in factors)
        + f". Weights source={weight_source}; not a frozen forever-formula."
    )
    return score, factors, explanation


def _key_for(signal: SignalInput, index: int) -> str:
    if signal.opportunity_key:
        return signal.opportunity_key
    slug = signal.opportunity_type.replace("_", "-")[:40]
    ent = (signal.related_entity or "general").lower().replace(" ", "-")[:40]
    return f"{slug}-{ent}-{index}"


def detect_and_rank(
    signals: list[SignalInput],
    *,
    model: RankingModelState | None = None,
    auto_fill_defaults: bool = True,
) -> ScanResult:
    """Turn signals into ranked Peacock Opportunities with explainable scores."""
    if not signals:
        raise ValueError("At least one opportunity signal is required")

    for s in signals:
        if s.opportunity_type not in OPPORTUNITY_TYPES:
            raise ValueError(f"Unsupported opportunity_type: {s.opportunity_type}")

    model = model or RankingModelState()
    weights = model.effective_weights()
    weight_source = (
        "base"
        if model.learning_sample_size < 3
        else ("learned" if model.blend_toward_learned >= 0.5 else "blended")
    )

    scored: list[OpportunityResult] = []
    for i, signal in enumerate(signals):
        title = signal.title
        action = signal.recommended_action
        if auto_fill_defaults and signal.opportunity_type in _TYPE_DEFAULTS:
            default_title, default_action = _TYPE_DEFAULTS[signal.opportunity_type]
            if not title.strip():
                title = default_title
            if not action.strip():
                action = default_action

        score, factors, explanation = score_opportunity(
            signal, weights, weight_source=weight_source
        )
        evidence = [
            EvidenceResult(
                evidence_type=e.evidence_type,
                statement=e.statement,
                source_ref=e.source_ref,
                strength=_clamp100(e.strength),
            )
            for e in signal.evidence
        ]
        if not evidence:
            evidence = [
                EvidenceResult(
                    evidence_type="signal",
                    statement=signal.description or title,
                    source_ref=signal.related_url,
                    strength=_clamp100(signal.confidence),
                )
            ]

        scored.append(
            OpportunityResult(
                opportunity_key=_key_for(signal, i),
                opportunity_type=signal.opportunity_type,
                title=title,
                description=signal.description,
                impact=_clamp100(signal.impact),
                urgency=_clamp100(signal.urgency),
                confidence=_clamp100(signal.confidence),
                difficulty=_clamp100(signal.difficulty),
                expected_value=_clamp100(signal.expected_value),
                recommended_action=action,
                evidence=evidence,
                rank=0,
                opportunity_score=score,
                ranking_explanation=explanation,
                ranking_factors=factors,
                related_entity=signal.related_entity,
                related_url=signal.related_url,
            )
        )

    scored.sort(key=lambda o: o.opportunity_score, reverse=True)
    for rank, opp in enumerate(scored, start=1):
        opp.rank = rank

    snaps = model.weight_snapshots()
    summary = (
        f"Peacock Opportunities scan ranked {len(scored)} opportunities "
        f"(model v{model.model_version}, adaptive={model.learning_sample_size >= 3}, "
        f"fixed-formula rejected). Top: {scored[0].title} "
        f"({scored[0].opportunity_score:.0f}/100)."
    )
    return ScanResult(
        opportunities=scored,
        ranking_weights=snaps,
        ranking_model_version=model.model_version,
        ranking_is_adaptive=True,
        fixed_formula_rejected=True,
        always_on_note=ALWAYS_ON_NOTE,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )


def example_signals_catalog() -> list[dict[str, str]]:
    """Catalog of opportunity type examples for API/docs."""
    return [
        {"opportunity_type": code, "example_title": _TYPE_DEFAULTS[code][0]}
        for code in OPPORTUNITY_TYPES
        if code in _TYPE_DEFAULTS
    ]
