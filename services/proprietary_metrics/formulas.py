"""Documented formulas for every Peacock proprietary metric.

IMPORTANT: These are Peacock proprietary indicators — never Google, OpenAI,
Anthropic, Perplexity, or other official ranking factors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from db_models.proprietary_metrics import (
    METRIC_KEYS,
    METRIC_LABELS,
    NOT_OFFICIAL_PLATFORMS,
    PROPRIETARY_DISCLAIMER,
)


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _clamp100(x: float) -> float:
    return max(0.0, min(100.0, float(x)))


def _norm_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, w) for w in weights.values()) or 1.0
    return {k: max(0.0, w) / total for k, w in weights.items()}


@dataclass(slots=True)
class FormulaDoc:
    formula_id: str
    metric_key: str
    metric_label: str
    unit: str
    formula_text: str
    range_note: str
    components: list[str]
    proprietary_note: str


@dataclass
class ComponentInput:
    key: str
    label: str
    value: float  # typically 0–100 or 0–1 depending on metric
    weight: float = 0.0


@dataclass
class MetricComputation:
    metric_key: str
    metric_label: str
    score: float
    unit: str
    formula_id: str
    formula_text: str
    explanation: str
    proprietary_note: str
    components: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_key": self.metric_key,
            "metric_label": self.metric_label,
            "score": self.score,
            "unit": self.unit,
            "formula_id": self.formula_id,
            "formula_text": self.formula_text,
            "explanation": self.explanation,
            "proprietary_note": self.proprietary_note,
            "components": self.components,
        }


# ---------------------------------------------------------------------------
# Formula registry (source of truth for documentation)
# ---------------------------------------------------------------------------

FORMULA_DOCS: dict[str, FormulaDoc] = {
    "peacock_visibility_index": FormulaDoc(
        formula_id="PVI-1",
        metric_key="peacock_visibility_index",
        metric_label=METRIC_LABELS["peacock_visibility_index"],
        unit="0-100",
        formula_text=(
            "PVI = mean(Search Visibility, AI Visibility, Share of Answer, "
            "Entity Authority, Citation Authority, Content Opportunity, Agent Readiness)"
        ),
        range_note="Equal-weight mean of seven Peacock dimensions; each dimension 0–100.",
        components=[
            "search_visibility",
            "ai_visibility",
            "share_of_answer",
            "entity_authority",
            "citation_authority",
            "content_opportunity",
            "agent_readiness",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "peacock_ai_visibility_score": FormulaDoc(
        formula_id="PAIVS-1",
        metric_key="peacock_ai_visibility_score",
        metric_label=METRIC_LABELS["peacock_ai_visibility_score"],
        unit="0-100",
        formula_text=(
            "PAIVS = 100 * (0.35*SoA_norm + 0.25*CIS_norm + 0.20*EntityAuth_norm "
            "+ 0.20*Citability_norm)"
        ),
        range_note="Composite of Peacock SoA, CIS, Entity Authority, Generative Citability (each normalised 0–1).",
        components=["share_of_answer", "citation_influence", "entity_authority", "citability"],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "share_of_answer": FormulaDoc(
        formula_id="SOA-1",
        metric_key="share_of_answer",
        metric_label=METRIC_LABELS["share_of_answer"],
        unit="0-100",
        formula_text=(
            "SoA = 100 * Σ_i (w_i * indicator_i) where indicators are mention, position, "
            "recommendation_strength, answer_space, citation_ownership, semantic_prominence, "
            "claim_balance, comparison_outcome; Σ w_i = 1. Token count alone is rejected."
        ),
        range_note="Default weights: mention 0.12, position 0.14, recommendation_strength 0.18, "
        "answer_space 0.10, citation_ownership 0.14, semantic_prominence 0.12, "
        "claim_balance 0.10, comparison_outcome 0.10.",
        components=[
            "mention",
            "position",
            "recommendation_strength",
            "answer_space",
            "citation_ownership",
            "semantic_prominence",
            "claim_balance",
            "comparison_outcome",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "citation_influence_score": FormulaDoc(
        formula_id="CIS-1",
        metric_key="citation_influence_score",
        metric_label=METRIC_LABELS["citation_influence_score"],
        unit="0-100",
        formula_text=(
            "CIS = 100 * Σ_i (w_i * component_i) with components citation_frequency, "
            "cross_engine_citation, topic_coverage, prominence, freshness, authority_proxy, "
            "brand_association, citation_diversity; Σ w_i = 1."
        ),
        range_note="Default weights: 0.18, 0.14, 0.12, 0.12, 0.10, 0.12, 0.12, 0.10 respectively.",
        components=[
            "citation_frequency",
            "cross_engine_citation",
            "topic_coverage",
            "prominence",
            "freshness",
            "authority_proxy",
            "brand_association",
            "citation_diversity",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "entity_authority_score": FormulaDoc(
        formula_id="EAS-1",
        metric_key="entity_authority_score",
        metric_label=METRIC_LABELS["entity_authority_score"],
        unit="0-100",
        formula_text=(
            "EAS = 100 * Σ_i (w_i * association_i) with co_occurrence, semantic_proximity, "
            "ownership_signal, citation_linkage, topical_centrality, recency, "
            "cross_source_consistency; Σ w_i = 1."
        ),
        range_note="Default weights: 0.20, 0.16, 0.18, 0.12, 0.12, 0.10, 0.12 respectively.",
        components=[
            "co_occurrence",
            "semantic_proximity",
            "ownership_signal",
            "citation_linkage",
            "topical_centrality",
            "recency",
            "cross_source_consistency",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "answer_readiness_score": FormulaDoc(
        formula_id="ARS-1",
        metric_key="answer_readiness_score",
        metric_label=METRIC_LABELS["answer_readiness_score"],
        unit="0-100",
        formula_text=(
            "ARS = 100 * (0.25*direct_answer_clarity + 0.20*evidence_density + "
            "0.20*structure_for_extraction + 0.20*entity_clarity + 0.15*freshness_signal)"
        ),
        range_note="Each input normalised 0–1 before weighting.",
        components=[
            "direct_answer_clarity",
            "evidence_density",
            "structure_for_extraction",
            "entity_clarity",
            "freshness_signal",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "generative_citability_score": FormulaDoc(
        formula_id="GCS-1",
        metric_key="generative_citability_score",
        metric_label=METRIC_LABELS["generative_citability_score"],
        unit="0-100",
        formula_text=(
            "GCS = mean(specificity, evidence, direct_answers, original_information, "
            "entity_clarity, source_attribution, freshness, structured_information, "
            "tables, definitions, comparisons) on 0–100 scale"
        ),
        range_note="Equal-weight mean of eleven citability components (0–100 each).",
        components=[
            "specificity",
            "evidence",
            "direct_answers",
            "original_information",
            "entity_clarity",
            "source_attribution",
            "freshness",
            "structured_information",
            "tables",
            "definitions",
            "comparisons",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "content_moat_score": FormulaDoc(
        formula_id="CMS-1",
        metric_key="content_moat_score",
        metric_label=METRIC_LABELS["content_moat_score"],
        unit="0-100",
        formula_text=(
            "CMS = clamp100(format_prior + 0.12 * (information_gain_score - 50)) "
            "where format_prior ∈ {generic_listicle:18, expert_interview:51, "
            "original_dataset:86, proprietary_benchmark_study:94, ...}"
        ),
        range_note="Format prior 0–100 plus information-gain nudge; clamped to 0–100.",
        components=["format_prior", "information_gain_score"],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "topic_opportunity_score": FormulaDoc(
        formula_id="TOS-1",
        metric_key="topic_opportunity_score",
        metric_label=METRIC_LABELS["topic_opportunity_score"],
        unit="0-100",
        formula_text=(
            "TOS = 0.25*impact + 0.20*urgency + 0.15*confidence + 0.30*expected_value "
            "+ 0.10*(100 - difficulty)"
        ),
        range_note="All inputs 0–100; difficulty inverted so lower difficulty raises score.",
        components=["impact", "urgency", "confidence", "expected_value", "difficulty"],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "writer_match_score": FormulaDoc(
        formula_id="WMS-1",
        metric_key="writer_match_score",
        metric_label=METRIC_LABELS["writer_match_score"],
        unit="0-100",
        formula_text=(
            "WMS = 0.28*dna_fit + 0.22*topic_fit + 0.18*client_fit + 0.12*audience_fit "
            "+ 0.20*historical_outcome; similarity-only matching is rejected"
        ),
        range_note="Predicted outcome-style fit 0–100; not resume/keyword similarity alone.",
        components=[
            "dna_fit",
            "topic_fit",
            "client_fit",
            "audience_fit",
            "historical_outcome",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "agent_readiness_score": FormulaDoc(
        formula_id="AGRS-1",
        metric_key="agent_readiness_score",
        metric_label=METRIC_LABELS["agent_readiness_score"],
        unit="0-100",
        formula_text=(
            "AGRS = Σ_i (w_i * check_score_i) / Σ_i w_i over agentic readiness checks "
            "(structured product info, pricing clarity, policies, machine-readable facts, "
            "trust signals, etc.)"
        ),
        range_note="Weighted average of check scores 0–100; proprietary Peacock surface, "
        "separate from SEO/AEO/GEO and not an industry-standard claim.",
        components=["weighted_check_average"],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "competitive_threat_score": FormulaDoc(
        formula_id="CTS-1",
        metric_key="competitive_threat_score",
        metric_label=METRIC_LABELS["competitive_threat_score"],
        unit="0-100",
        formula_text=(
            "CTS = 100 * (0.30*citation_share_gap + 0.25*soa_gap + 0.20*content_velocity "
            "+ 0.15*entity_coverage_gap + 0.10*recent_acceleration) "
            "with each factor normalised 0–1"
        ),
        range_note="Higher = greater competitive threat on generative surfaces.",
        components=[
            "citation_share_gap",
            "soa_gap",
            "content_velocity",
            "entity_coverage_gap",
            "recent_acceleration",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
    "opportunity_confidence": FormulaDoc(
        formula_id="OC-1",
        metric_key="opportunity_confidence",
        metric_label=METRIC_LABELS["opportunity_confidence"],
        unit="0-1",
        formula_text=(
            "OC = clamp01(0.40*evidence_coverage + 0.30*signal_agreement + "
            "0.20*data_recency + 0.10*sample_adequacy)"
        ),
        range_note="0–1 confidence in an opportunity recommendation; not win probability guarantee.",
        components=[
            "evidence_coverage",
            "signal_agreement",
            "data_recency",
            "sample_adequacy",
        ],
        proprietary_note=PROPRIETARY_DISCLAIMER,
    ),
}


DEFAULT_WEIGHTS: dict[str, dict[str, float]] = {
    "share_of_answer": {
        "mention": 0.12,
        "position": 0.14,
        "recommendation_strength": 0.18,
        "answer_space": 0.10,
        "citation_ownership": 0.14,
        "semantic_prominence": 0.12,
        "claim_balance": 0.10,
        "comparison_outcome": 0.10,
    },
    "citation_influence_score": {
        "citation_frequency": 0.18,
        "cross_engine_citation": 0.14,
        "topic_coverage": 0.12,
        "prominence": 0.12,
        "freshness": 0.10,
        "authority_proxy": 0.12,
        "brand_association": 0.12,
        "citation_diversity": 0.10,
    },
    "entity_authority_score": {
        "co_occurrence": 0.20,
        "semantic_proximity": 0.16,
        "ownership_signal": 0.18,
        "citation_linkage": 0.12,
        "topical_centrality": 0.12,
        "recency": 0.10,
        "cross_source_consistency": 0.12,
    },
    "answer_readiness_score": {
        "direct_answer_clarity": 0.25,
        "evidence_density": 0.20,
        "structure_for_extraction": 0.20,
        "entity_clarity": 0.20,
        "freshness_signal": 0.15,
    },
    "peacock_ai_visibility_score": {
        "share_of_answer": 0.35,
        "citation_influence": 0.25,
        "entity_authority": 0.20,
        "citability": 0.20,
    },
    "topic_opportunity_score": {
        "impact": 0.25,
        "urgency": 0.20,
        "confidence": 0.15,
        "expected_value": 0.30,
        "difficulty": 0.10,  # applied as (100 - difficulty)
    },
    "writer_match_score": {
        "dna_fit": 0.28,
        "topic_fit": 0.22,
        "client_fit": 0.18,
        "audience_fit": 0.12,
        "historical_outcome": 0.20,
    },
    "competitive_threat_score": {
        "citation_share_gap": 0.30,
        "soa_gap": 0.25,
        "content_velocity": 0.20,
        "entity_coverage_gap": 0.15,
        "recent_acceleration": 0.10,
    },
    "opportunity_confidence": {
        "evidence_coverage": 0.40,
        "signal_agreement": 0.30,
        "data_recency": 0.20,
        "sample_adequacy": 0.10,
    },
}


def formula_catalog() -> dict[str, Any]:
    return {
        "metric_keys": list(METRIC_KEYS),
        "metric_labels": dict(METRIC_LABELS),
        "proprietary_disclaimer": PROPRIETARY_DISCLAIMER,
        "not_official_platforms": list(NOT_OFFICIAL_PLATFORMS),
        "formulas": [
            {
                "formula_id": d.formula_id,
                "metric_key": d.metric_key,
                "metric_label": d.metric_label,
                "unit": d.unit,
                "formula_text": d.formula_text,
                "range_note": d.range_note,
                "components": list(d.components),
                "proprietary_note": d.proprietary_note,
            }
            for d in (FORMULA_DOCS[k] for k in METRIC_KEYS)
        ],
        "default_weights": DEFAULT_WEIGHTS,
        "important": (
            "Never represent Peacock Proprietary Metrics as Google, OpenAI, Anthropic, "
            "Perplexity, or other official ranking factors."
        ),
    }


def _weighted_from_0_100(
    *,
    metric_key: str,
    values: dict[str, float],
    weights: dict[str, float],
    invert_keys: set[str] | None = None,
) -> MetricComputation:
    doc = FORMULA_DOCS[metric_key]
    invert_keys = invert_keys or set()
    w = _norm_weights(weights)
    comps: list[dict[str, Any]] = []
    score = 0.0
    for i, (key, weight) in enumerate(w.items()):
        raw = float(values.get(key, 50.0))
        effective = (100.0 - raw) if key in invert_keys else raw
        effective = _clamp100(effective)
        contrib = weight * effective
        score += contrib
        comps.append(
            {
                "component_key": key,
                "component_label": key.replace("_", " ").title(),
                "raw_value": round(raw, 4),
                "weight": round(weight, 4),
                "contribution": round(contrib, 4),
                "rank_order": i,
            }
        )
    return MetricComputation(
        metric_key=metric_key,
        metric_label=doc.metric_label,
        score=round(_clamp100(score), 2),
        unit=doc.unit,
        formula_id=doc.formula_id,
        formula_text=doc.formula_text,
        explanation=doc.range_note,
        proprietary_note=doc.proprietary_note,
        components=comps,
    )


def _weighted_from_0_1(
    *,
    metric_key: str,
    values: dict[str, float],
    weights: dict[str, float],
    scale_100: bool,
) -> MetricComputation:
    doc = FORMULA_DOCS[metric_key]
    w = _norm_weights(weights)
    comps: list[dict[str, Any]] = []
    score01 = 0.0
    for i, (key, weight) in enumerate(w.items()):
        raw = float(values.get(key, 0.5))
        # accept 0–100 or 0–1
        norm = _clamp01(raw / 100.0 if raw > 1.0 else raw)
        contrib = weight * norm
        score01 += contrib
        comps.append(
            {
                "component_key": key,
                "component_label": key.replace("_", " ").title(),
                "raw_value": round(norm, 4),
                "weight": round(weight, 4),
                "contribution": round(contrib, 4),
                "rank_order": i,
            }
        )
    score = round(100.0 * _clamp01(score01), 2) if scale_100 else round(_clamp01(score01), 4)
    return MetricComputation(
        metric_key=metric_key,
        metric_label=doc.metric_label,
        score=score,
        unit=doc.unit,
        formula_id=doc.formula_id,
        formula_text=doc.formula_text,
        explanation=doc.range_note,
        proprietary_note=doc.proprietary_note,
        components=comps,
    )


def compute_peacock_visibility_index(dimensions: dict[str, float]) -> MetricComputation:
    doc = FORMULA_DOCS["peacock_visibility_index"]
    keys = doc.components
    vals = [_clamp100(float(dimensions.get(k, 50.0))) for k in keys]
    score = round(sum(vals) / len(vals), 2) if vals else 0.0
    comps = [
        {
            "component_key": k,
            "component_label": k.replace("_", " ").title(),
            "raw_value": round(v, 4),
            "weight": round(1.0 / len(keys), 4),
            "contribution": round(v / len(keys), 4),
            "rank_order": i,
        }
        for i, (k, v) in enumerate(zip(keys, vals, strict=True))
    ]
    return MetricComputation(
        metric_key=doc.metric_key,
        metric_label=doc.metric_label,
        score=score,
        unit=doc.unit,
        formula_id=doc.formula_id,
        formula_text=doc.formula_text,
        explanation=doc.range_note,
        proprietary_note=doc.proprietary_note,
        components=comps,
    )


def compute_content_moat(format_prior: float, information_gain_score: float) -> MetricComputation:
    doc = FORMULA_DOCS["content_moat_score"]
    prior = _clamp100(format_prior)
    ig = _clamp100(information_gain_score)
    score = round(_clamp100(prior + 0.12 * (ig - 50.0)), 2)
    comps = [
        {
            "component_key": "format_prior",
            "component_label": "Format Prior",
            "raw_value": prior,
            "weight": 1.0,
            "contribution": prior,
            "rank_order": 0,
        },
        {
            "component_key": "information_gain_score",
            "component_label": "Information Gain Score",
            "raw_value": ig,
            "weight": 0.12,
            "contribution": round(0.12 * (ig - 50.0), 4),
            "rank_order": 1,
        },
    ]
    return MetricComputation(
        metric_key=doc.metric_key,
        metric_label=doc.metric_label,
        score=score,
        unit=doc.unit,
        formula_id=doc.formula_id,
        formula_text=doc.formula_text,
        explanation=doc.range_note,
        proprietary_note=doc.proprietary_note,
        components=comps,
    )


def compute_generative_citability(components: dict[str, float]) -> MetricComputation:
    doc = FORMULA_DOCS["generative_citability_score"]
    keys = doc.components
    vals = [_clamp100(float(components.get(k, 50.0))) for k in keys]
    score = round(sum(vals) / len(vals), 2)
    weight = 1.0 / len(keys)
    comps = [
        {
            "component_key": k,
            "component_label": k.replace("_", " ").title(),
            "raw_value": round(v, 4),
            "weight": round(weight, 4),
            "contribution": round(v * weight, 4),
            "rank_order": i,
        }
        for i, (k, v) in enumerate(zip(keys, vals, strict=True))
    ]
    return MetricComputation(
        metric_key=doc.metric_key,
        metric_label=doc.metric_label,
        score=score,
        unit=doc.unit,
        formula_id=doc.formula_id,
        formula_text=doc.formula_text,
        explanation=doc.range_note,
        proprietary_note=doc.proprietary_note,
        components=comps,
    )


def compute_agent_readiness(check_scores: dict[str, float], check_weights: dict[str, float] | None = None) -> MetricComputation:
    doc = FORMULA_DOCS["agent_readiness_score"]
    if not check_scores:
        check_scores = {"overall": 54.0}
    weights = check_weights or {k: 1.0 for k in check_scores}
    w = _norm_weights({k: weights.get(k, 1.0) for k in check_scores})
    score = 0.0
    comps: list[dict[str, Any]] = []
    for i, (key, weight) in enumerate(w.items()):
        raw = _clamp100(float(check_scores[key]))
        contrib = weight * raw
        score += contrib
        comps.append(
            {
                "component_key": key,
                "component_label": key.replace("_", " ").title(),
                "raw_value": round(raw, 4),
                "weight": round(weight, 4),
                "contribution": round(contrib, 4),
                "rank_order": i,
            }
        )
    return MetricComputation(
        metric_key=doc.metric_key,
        metric_label=doc.metric_label,
        score=round(_clamp100(score), 2),
        unit=doc.unit,
        formula_id=doc.formula_id,
        formula_text=doc.formula_text,
        explanation=doc.range_note,
        proprietary_note=doc.proprietary_note,
        components=comps,
    )
