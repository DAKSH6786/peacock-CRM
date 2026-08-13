"""Scorecard assembly for Peacock Proprietary Metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from db_models.proprietary_metrics import (
    METHODOLOGY_NOTE,
    METRIC_KEYS,
    NOT_OFFICIAL_PLATFORMS,
    PROPRIETARY_DISCLAIMER,
)
from proprietary_metrics.formulas import (
    DEFAULT_WEIGHTS,
    MetricComputation,
    compute_agent_readiness,
    compute_content_moat,
    compute_generative_citability,
    compute_peacock_visibility_index,
    formula_catalog,
    _weighted_from_0_1,
    _weighted_from_0_100,
)


@dataclass
class MetricInputs:
    """Optional overrides; missing values use demo defaults."""

    visibility_dimensions: dict[str, float] = field(default_factory=dict)
    soa_indicators: dict[str, float] = field(default_factory=dict)
    cis_components: dict[str, float] = field(default_factory=dict)
    entity_components: dict[str, float] = field(default_factory=dict)
    answer_readiness: dict[str, float] = field(default_factory=dict)
    citability_components: dict[str, float] = field(default_factory=dict)
    moat_format_prior: float | None = None
    moat_information_gain: float | None = None
    topic_opportunity: dict[str, float] = field(default_factory=dict)
    writer_match: dict[str, float] = field(default_factory=dict)
    agent_checks: dict[str, float] = field(default_factory=dict)
    competitive_threat: dict[str, float] = field(default_factory=dict)
    opportunity_confidence: dict[str, float] = field(default_factory=dict)
    ai_visibility_parts: dict[str, float] = field(default_factory=dict)


@dataclass
class ProprietaryMetricsSpec:
    client_brand: str
    inputs: MetricInputs = field(default_factory=MetricInputs)
    scored_at: datetime | None = None


@dataclass
class ProprietaryMetricsResult:
    client_brand: str
    scored_at: datetime
    metrics: list[MetricComputation]
    metrics_scored: int
    proprietary_disclaimer: str
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "scored_at": self.scored_at.isoformat(),
            "metrics": [m.to_dict() for m in self.metrics],
            "metrics_scored": self.metrics_scored,
            "proprietary_disclaimer": self.proprietary_disclaimer,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
            "not_official_platforms": list(NOT_OFFICIAL_PLATFORMS),
        }


def catalog() -> dict[str, Any]:
    base = formula_catalog()
    base["methodology_note"] = METHODOLOGY_NOTE
    return base


def demo_inputs() -> MetricInputs:
    return MetricInputs(
        visibility_dimensions={
            "search_visibility": 72,
            "ai_visibility": 58,
            "share_of_answer": 41,
            "entity_authority": 63,
            "citation_authority": 47,
            "content_opportunity": 81,
            "agent_readiness": 54,
        },
        soa_indicators={
            "mention": 70,
            "position": 55,
            "recommendation_strength": 48,
            "answer_space": 52,
            "citation_ownership": 40,
            "semantic_prominence": 50,
            "claim_balance": 58,
            "comparison_outcome": 35,
        },
        cis_components={
            "citation_frequency": 44,
            "cross_engine_citation": 38,
            "topic_coverage": 55,
            "prominence": 42,
            "freshness": 60,
            "authority_proxy": 50,
            "brand_association": 48,
            "citation_diversity": 46,
        },
        entity_components={
            "co_occurrence": 62,
            "semantic_proximity": 58,
            "ownership_signal": 70,
            "citation_linkage": 45,
            "topical_centrality": 60,
            "recency": 55,
            "cross_source_consistency": 57,
        },
        answer_readiness={
            "direct_answer_clarity": 0.62,
            "evidence_density": 0.55,
            "structure_for_extraction": 0.48,
            "entity_clarity": 0.66,
            "freshness_signal": 0.50,
        },
        citability_components={
            "specificity": 58,
            "evidence": 52,
            "direct_answers": 60,
            "original_information": 45,
            "entity_clarity": 64,
            "source_attribution": 50,
            "freshness": 55,
            "structured_information": 48,
            "tables": 40,
            "definitions": 62,
            "comparisons": 35,
        },
        moat_format_prior=51,
        moat_information_gain=62,
        topic_opportunity={
            "impact": 78,
            "urgency": 72,
            "confidence": 68,
            "expected_value": 74,
            "difficulty": 45,
        },
        writer_match={
            "dna_fit": 82,
            "topic_fit": 76,
            "client_fit": 70,
            "audience_fit": 68,
            "historical_outcome": 74,
        },
        agent_checks={
            "structured_product_information": 60,
            "clear_pricing": 55,
            "machine_readable_facts": 48,
            "trust_signals": 58,
            "policy_clarity": 52,
        },
        competitive_threat={
            "citation_share_gap": 0.72,
            "soa_gap": 0.65,
            "content_velocity": 0.58,
            "entity_coverage_gap": 0.55,
            "recent_acceleration": 0.80,
        },
        opportunity_confidence={
            "evidence_coverage": 0.78,
            "signal_agreement": 0.70,
            "data_recency": 0.82,
            "sample_adequacy": 0.60,
        },
    )


def score_proprietary_metrics(spec: ProprietaryMetricsSpec) -> ProprietaryMetricsResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")

    demo = demo_inputs()
    inp = spec.inputs

    vis_dims = inp.visibility_dimensions or demo.visibility_dimensions
    soa = inp.soa_indicators or demo.soa_indicators
    cis = inp.cis_components or demo.cis_components
    entity = inp.entity_components or demo.entity_components
    ars = inp.answer_readiness or demo.answer_readiness
    cit = inp.citability_components or demo.citability_components
    moat_prior = (
        demo.moat_format_prior
        if inp.moat_format_prior is None
        else inp.moat_format_prior
    )
    moat_ig = (
        demo.moat_information_gain
        if inp.moat_information_gain is None
        else inp.moat_information_gain
    )
    topic = inp.topic_opportunity or demo.topic_opportunity
    writer = inp.writer_match or demo.writer_match
    agent = inp.agent_checks or demo.agent_checks
    threat = inp.competitive_threat or demo.competitive_threat
    opp_conf = inp.opportunity_confidence or demo.opportunity_confidence

    soa_m = _weighted_from_0_100(
        metric_key="share_of_answer",
        values=soa,
        weights=DEFAULT_WEIGHTS["share_of_answer"],
    )
    cis_m = _weighted_from_0_100(
        metric_key="citation_influence_score",
        values=cis,
        weights=DEFAULT_WEIGHTS["citation_influence_score"],
    )
    eas_m = _weighted_from_0_100(
        metric_key="entity_authority_score",
        values=entity,
        weights=DEFAULT_WEIGHTS["entity_authority_score"],
    )
    gcs_m = compute_generative_citability(cit)
    ars_m = _weighted_from_0_1(
        metric_key="answer_readiness_score",
        values=ars,
        weights=DEFAULT_WEIGHTS["answer_readiness_score"],
        scale_100=True,
    )
    cms_m = compute_content_moat(float(moat_prior or 0), float(moat_ig or 0))
    tos_m = _weighted_from_0_100(
        metric_key="topic_opportunity_score",
        values=topic,
        weights=DEFAULT_WEIGHTS["topic_opportunity_score"],
        invert_keys={"difficulty"},
    )
    wms_m = _weighted_from_0_100(
        metric_key="writer_match_score",
        values=writer,
        weights=DEFAULT_WEIGHTS["writer_match_score"],
    )
    agrs_m = compute_agent_readiness(agent)
    cts_m = _weighted_from_0_1(
        metric_key="competitive_threat_score",
        values=threat,
        weights=DEFAULT_WEIGHTS["competitive_threat_score"],
        scale_100=True,
    )
    oc_m = _weighted_from_0_1(
        metric_key="opportunity_confidence",
        values=opp_conf,
        weights=DEFAULT_WEIGHTS["opportunity_confidence"],
        scale_100=False,
    )

    ai_parts = inp.ai_visibility_parts or {
        "share_of_answer": soa_m.score,
        "citation_influence": cis_m.score,
        "entity_authority": eas_m.score,
        "citability": gcs_m.score,
    }
    paivs_m = _weighted_from_0_1(
        metric_key="peacock_ai_visibility_score",
        values=ai_parts,
        weights=DEFAULT_WEIGHTS["peacock_ai_visibility_score"],
        scale_100=True,
    )

    # Align visibility dimensions with computed SoA / agent if not overridden fully
    dims = dict(vis_dims)
    dims.setdefault("share_of_answer", soa_m.score)
    dims.setdefault("agent_readiness", agrs_m.score)
    dims.setdefault("ai_visibility", paivs_m.score)
    dims.setdefault("entity_authority", eas_m.score)
    dims.setdefault("citation_authority", cis_m.score)
    pvi_m = compute_peacock_visibility_index(dims)

    by_key = {
        "peacock_visibility_index": pvi_m,
        "peacock_ai_visibility_score": paivs_m,
        "share_of_answer": soa_m,
        "citation_influence_score": cis_m,
        "entity_authority_score": eas_m,
        "answer_readiness_score": ars_m,
        "generative_citability_score": gcs_m,
        "content_moat_score": cms_m,
        "topic_opportunity_score": tos_m,
        "writer_match_score": wms_m,
        "agent_readiness_score": agrs_m,
        "competitive_threat_score": cts_m,
        "opportunity_confidence": oc_m,
    }
    metrics = [by_key[k] for k in METRIC_KEYS]
    scored_at = spec.scored_at or datetime.now(tz=UTC)
    summary = (
        f"Proprietary metrics scorecard for {brand}: {len(metrics)} documented "
        f"Peacock indicators. {PROPRIETARY_DISCLAIMER}"
    )
    return ProprietaryMetricsResult(
        client_brand=brand,
        scored_at=scored_at,
        metrics=metrics,
        metrics_scored=len(metrics),
        proprietary_disclaimer=PROPRIETARY_DISCLAIMER,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )
