"""Learning Engine 2.0 core — closed loop + industry-specific learning."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.learning_engine2 import (
    INDUSTRIES,
    INDUSTRY_LABELS,
    LEARNING_DIMENSIONS,
    METHODOLOGY_NOTE,
    NOT_UNIVERSAL_GEO,
)


SUCCESS_THRESHOLD = 0.0  # outcome_delta >= 0 counts as success


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


@dataclass
class ContextFactorInput:
    factor_key: str
    factor_value: str
    weight: float = 1.0


@dataclass
class LearningRecordSpec:
    name: str
    industry: str
    context_summary: str
    recommendation_text: str
    expected_impact: str
    expected_impact_score: float
    confidence: float
    topic_key: str | None = None
    format_key: str | None = None
    source_key: str | None = None
    writer_key: str | None = None
    intervention_key: str | None = None
    engine_key: str | None = None
    context_factors: list[ContextFactorInput] = field(default_factory=list)
    central_recommendation_id: str | None = None
    notes: str | None = None

    def validate(self) -> None:
        if self.industry not in INDUSTRIES:
            raise ValueError(f"Unsupported industry: {self.industry}")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.context_summary.strip():
            raise ValueError("context_summary is required")
        if not self.recommendation_text.strip():
            raise ValueError("recommendation_text is required")
        if not self.expected_impact.strip():
            raise ValueError("expected_impact is required")
        if not (0.0 <= self.expected_impact_score <= 100.0):
            raise ValueError("expected_impact_score must be 0–100")
        if not (0.0 <= self.confidence <= 100.0):
            raise ValueError("confidence must be 0–100")


@dataclass
class ExecutionUpdate:
    execution_summary: str
    execution_status: str = "executed"


@dataclass
class OutcomeUpdate:
    actual_outcome: str
    actual_outcome_score: float

    def validate(self) -> None:
        if not self.actual_outcome.strip():
            raise ValueError("actual_outcome is required")
        if not (0.0 <= self.actual_outcome_score <= 100.0):
            raise ValueError("actual_outcome_score must be 0–100")


@dataclass(slots=True)
class ContextFactorResult:
    factor_key: str
    factor_value: str
    weight: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LearningRecordView:
    name: str
    industry: str
    record_status: str
    context_summary: str
    recommendation_text: str
    expected_impact: str
    expected_impact_score: float
    confidence: float
    execution_summary: str | None
    execution_status: str | None
    actual_outcome: str | None
    actual_outcome_score: float | None
    outcome_delta: float | None
    topic_key: str | None
    format_key: str | None
    source_key: str | None
    writer_key: str | None
    intervention_key: str | None
    engine_key: str | None
    context_factors: list[ContextFactorResult]
    not_universal_geo_strategy: bool
    not_universal_geo_note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **{
                k: getattr(self, k)
                for k in (
                    "name",
                    "industry",
                    "record_status",
                    "context_summary",
                    "recommendation_text",
                    "expected_impact",
                    "expected_impact_score",
                    "confidence",
                    "execution_summary",
                    "execution_status",
                    "actual_outcome",
                    "actual_outcome_score",
                    "outcome_delta",
                    "topic_key",
                    "format_key",
                    "source_key",
                    "writer_key",
                    "intervention_key",
                    "engine_key",
                    "not_universal_geo_strategy",
                    "not_universal_geo_note",
                )
            },
            "context_factors": [c.to_dict() for c in self.context_factors],
        }


@dataclass(slots=True)
class DimensionInsightResult:
    dimension: str
    dimension_key: str
    industry: str
    sample_size: int
    avg_expected_impact: float
    avg_actual_outcome: float
    avg_confidence: float
    success_rate: float
    insight_summary: str
    not_universal_geo_strategy: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IndustryPolicyResult:
    industry: str
    industry_label: str
    policy_code: str
    title: str
    guidance: str
    preferred_formats: list[str]
    preferred_sources: list[str]
    citation_interventions: list[str]
    forbidden_universal_claims: str
    sample_size: int
    success_rate: float | None
    active: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LearningRunResult:
    records_considered: int
    insights: list[DimensionInsightResult]
    industry_policies: list[IndustryPolicyResult]
    industries_touched: list[str]
    not_universal_geo_strategy: bool
    methodology_note: str
    learning_questions: dict[str, str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "records_considered": self.records_considered,
            "insights": [i.to_dict() for i in self.insights],
            "industry_policies": [p.to_dict() for p in self.industry_policies],
            "industries_touched": list(self.industries_touched),
            "not_universal_geo_strategy": True,
            "methodology_note": self.methodology_note,
            "learning_questions": dict(self.learning_questions),
            "summary": self.summary,
        }


def default_industry_policies() -> list[IndustryPolicyResult]:
    """Seed industry-specific GEO/content policies — never a single universal policy."""
    seeds: dict[str, dict[str, Any]] = {
        "finance": {
            "title": "Finance citation & compliance-aware GEO",
            "guidance": (
                "Prefer regulated disclosures, primary filings, and expert-attributed "
                "explainers. Avoid hype claims; emphasise provenance."
            ),
            "formats": ["regulatory_explainer", "data_table", "faq"],
            "sources": ["regulator", "primary_filing", "analyst_note"],
            "interventions": ["add_primary_source", "expert_byline", "risk_disclaimer"],
        },
        "healthcare": {
            "title": "Healthcare evidence-first GEO",
            "guidance": (
                "Prioritise clinical evidence, contraindications, and clinician review. "
                "Do not generalise consumer wellness tactics to clinical topics."
            ),
            "formats": ["evidence_summary", "patient_faq", "guideline_digest"],
            "sources": ["peer_reviewed", "guideline_body", "clinician"],
            "interventions": ["cite_study", "add_limitations", "medical_review"],
        },
        "saas": {
            "title": "SaaS product-led GEO",
            "guidance": (
                "Lead with product proofs, comparisons, and integration specifics. "
                "Category pages differ from consumer SEO playbooks."
            ),
            "formats": ["comparison", "integration_guide", "use_case"],
            "sources": ["docs", "customer_story", "changelog"],
            "interventions": ["add_proof", "structured_comparison", "api_examples"],
        },
        "ecommerce": {
            "title": "E-commerce offer & entity GEO",
            "guidance": (
                "Optimise product entities, offers, shipping/returns clarity. "
                "Do not copy B2B thought-leadership GEO wholesale."
            ),
            "formats": ["product_spec", "buying_guide", "offer_block"],
            "sources": ["manufacturer", "review_aggregate", "merchant"],
            "interventions": ["enrich_offer", "add_gtin", "clarify_shipping"],
        },
        "education": {
            "title": "Education curriculum-aligned GEO",
            "guidance": "Emphasise learning outcomes, accreditation, and syllabus clarity.",
            "formats": ["curriculum_outline", "outcome_list", "faq"],
            "sources": ["accreditation", "faculty", "syllabus"],
            "interventions": ["add_outcomes", "faculty_bio", "accreditation_mark"],
        },
        "travel": {
            "title": "Travel logistics & locality GEO",
            "guidance": "Surface locations, seasons, booking constraints, and safety notes.",
            "formats": ["itinerary", "local_guide", "booking_block"],
            "sources": ["destination_board", "operator", "traveler_review"],
            "interventions": ["add_hours", "seasonality", "booking_cta"],
        },
        "legal": {
            "title": "Legal jurisdiction-aware GEO",
            "guidance": (
                "Separate jurisdictions; avoid universal legal advice framing. "
                "Cite statutes and disclaimers carefully."
            ),
            "formats": ["jurisdiction_brief", "faq", "process_map"],
            "sources": ["statute", "case_law", "bar_guidance"],
            "interventions": ["add_jurisdiction", "disclaimer", "cite_statute"],
        },
        "consumer_goods": {
            "title": "Consumer goods trust & review GEO",
            "guidance": "Lean on ingredients/specs, safety, and verified reviews.",
            "formats": ["spec_sheet", "how_to", "review_digest"],
            "sources": ["lab_test", "retailer", "verified_review"],
            "interventions": ["add_ingredients", "safety_note", "review_schema"],
        },
        "technology": {
            "title": "Technology standards & docs GEO",
            "guidance": "Prefer standards, benchmarks, and reproducible technical detail.",
            "formats": ["benchmark", "architecture_note", "tutorial"],
            "sources": ["standards_body", "benchmark", "engineering_blog"],
            "interventions": ["add_benchmark", "repro_steps", "standards_cite"],
        },
    }
    out: list[IndustryPolicyResult] = []
    for code, data in seeds.items():
        out.append(
            IndustryPolicyResult(
                industry=code,
                industry_label=INDUSTRY_LABELS[code],
                policy_code=f"{code}_geo_default",
                title=data["title"],
                guidance=data["guidance"],
                preferred_formats=list(data["formats"]),
                preferred_sources=list(data["sources"]),
                citation_interventions=list(data["interventions"]),
                forbidden_universal_claims=NOT_UNIVERSAL_GEO,
                sample_size=0,
                success_rate=None,
                active=True,
            )
        )
    return out


def build_record_view(spec: LearningRecordSpec) -> LearningRecordView:
    spec.validate()
    return LearningRecordView(
        name=spec.name.strip(),
        industry=spec.industry,
        record_status="recommended",
        context_summary=spec.context_summary.strip(),
        recommendation_text=spec.recommendation_text.strip(),
        expected_impact=spec.expected_impact.strip(),
        expected_impact_score=_clamp100(spec.expected_impact_score),
        confidence=_clamp100(spec.confidence),
        execution_summary=None,
        execution_status=None,
        actual_outcome=None,
        actual_outcome_score=None,
        outcome_delta=None,
        topic_key=spec.topic_key,
        format_key=spec.format_key,
        source_key=spec.source_key,
        writer_key=spec.writer_key,
        intervention_key=spec.intervention_key,
        engine_key=spec.engine_key,
        context_factors=[
            ContextFactorResult(f.factor_key, f.factor_value, f.weight)
            for f in spec.context_factors
        ],
        not_universal_geo_strategy=True,
        not_universal_geo_note=NOT_UNIVERSAL_GEO,
    )


def apply_execution(view: LearningRecordView, update: ExecutionUpdate) -> LearningRecordView:
    if not update.execution_summary.strip():
        raise ValueError("execution_summary is required")
    return LearningRecordView(
        name=view.name,
        industry=view.industry,
        record_status="executed",
        context_summary=view.context_summary,
        recommendation_text=view.recommendation_text,
        expected_impact=view.expected_impact,
        expected_impact_score=view.expected_impact_score,
        confidence=view.confidence,
        execution_summary=update.execution_summary.strip(),
        execution_status=update.execution_status,
        actual_outcome=view.actual_outcome,
        actual_outcome_score=view.actual_outcome_score,
        outcome_delta=view.outcome_delta,
        topic_key=view.topic_key,
        format_key=view.format_key,
        source_key=view.source_key,
        writer_key=view.writer_key,
        intervention_key=view.intervention_key,
        engine_key=view.engine_key,
        context_factors=list(view.context_factors),
        not_universal_geo_strategy=True,
        not_universal_geo_note=view.not_universal_geo_note,
    )


def apply_outcome(view: LearningRecordView, update: OutcomeUpdate) -> LearningRecordView:
    update.validate()
    if view.execution_summary is None:
        raise ValueError("Cannot record outcome before execution")
    delta = update.actual_outcome_score - view.expected_impact_score
    return LearningRecordView(
        name=view.name,
        industry=view.industry,
        record_status="outcome_recorded",
        context_summary=view.context_summary,
        recommendation_text=view.recommendation_text,
        expected_impact=view.expected_impact,
        expected_impact_score=view.expected_impact_score,
        confidence=view.confidence,
        execution_summary=view.execution_summary,
        execution_status=view.execution_status,
        actual_outcome=update.actual_outcome.strip(),
        actual_outcome_score=_clamp100(update.actual_outcome_score),
        outcome_delta=round(delta, 2),
        topic_key=view.topic_key,
        format_key=view.format_key,
        source_key=view.source_key,
        writer_key=view.writer_key,
        intervention_key=view.intervention_key,
        engine_key=view.engine_key,
        context_factors=list(view.context_factors),
        not_universal_geo_strategy=True,
        not_universal_geo_note=view.not_universal_geo_note,
    )


def _dimension_pairs(rec: LearningRecordView) -> list[tuple[str, str]]:
    pairs = []
    mapping = {
        "topic": rec.topic_key,
        "format": rec.format_key,
        "source": rec.source_key,
        "writer": rec.writer_key,
        "citation_intervention": rec.intervention_key,
        "industry": rec.industry,
        "engine": rec.engine_key,
    }
    for dim, key in mapping.items():
        if key:
            pairs.append((dim, key))
    return pairs


def learn_from_records(records: list[LearningRecordView]) -> LearningRunResult:
    """Aggregate outcomes into dimension insights + refresh industry policies."""
    eligible = [
        r
        for r in records
        if r.actual_outcome_score is not None and r.record_status in (
            "outcome_recorded",
            "learned",
        )
    ]
    buckets: dict[tuple[str, str, str], list[LearningRecordView]] = defaultdict(list)
    for rec in eligible:
        for dim, key in _dimension_pairs(rec):
            buckets[(dim, key, rec.industry)].append(rec)
            # Also aggregate industry-agnostic slice carefully — still flag not universal
            if dim != "industry":
                buckets[(dim, key, "all")].append(rec)

    insights: list[DimensionInsightResult] = []
    for (dim, key, industry), group in sorted(buckets.items()):
        n = len(group)
        avg_exp = sum(g.expected_impact_score for g in group) / n
        avg_act = sum(g.actual_outcome_score or 0.0 for g in group) / n
        avg_conf = sum(g.confidence for g in group) / n
        successes = sum(
            1
            for g in group
            if (g.outcome_delta is not None and g.outcome_delta >= SUCCESS_THRESHOLD)
            or ((g.actual_outcome_score or 0) >= g.expected_impact_score)
        )
        success_rate = successes / n
        scope = (
            f"industry={INDUSTRY_LABELS.get(industry, industry)}"
            if industry != "all"
            else "cross-industry (not a universal GEO strategy)"
        )
        insights.append(
            DimensionInsightResult(
                dimension=dim,
                dimension_key=key,
                industry=industry,
                sample_size=n,
                avg_expected_impact=round(avg_exp, 1),
                avg_actual_outcome=round(avg_act, 1),
                avg_confidence=round(avg_conf, 1),
                success_rate=round(success_rate, 3),
                insight_summary=(
                    f"{dim}='{key}' ({scope}): n={n}, success_rate={success_rate:.0%}, "
                    f"avg actual {avg_act:.0f} vs expected {avg_exp:.0f}."
                ),
                not_universal_geo_strategy=True,
            )
        )

    # Refresh industry policies with observed success rates
    policies = default_industry_policies()
    by_industry: dict[str, list[LearningRecordView]] = defaultdict(list)
    for rec in eligible:
        by_industry[rec.industry].append(rec)
    refreshed: list[IndustryPolicyResult] = []
    for policy in policies:
        group = by_industry.get(policy.industry, [])
        if group:
            sr = sum(
                1
                for g in group
                if (g.actual_outcome_score or 0) >= g.expected_impact_score
            ) / len(group)
            # Prefer formats/sources that worked in this industry
            format_wins = [
                i
                for i in insights
                if i.dimension == "format"
                and i.industry == policy.industry
                and i.success_rate >= 0.5
            ]
            source_wins = [
                i
                for i in insights
                if i.dimension == "source"
                and i.industry == policy.industry
                and i.success_rate >= 0.5
            ]
            intervention_wins = [
                i
                for i in insights
                if i.dimension == "citation_intervention"
                and i.industry == policy.industry
                and i.success_rate >= 0.5
            ]
            preferred_formats = (
                [i.dimension_key for i in format_wins] or policy.preferred_formats
            )
            preferred_sources = (
                [i.dimension_key for i in source_wins] or policy.preferred_sources
            )
            interventions = (
                [i.dimension_key for i in intervention_wins]
                or policy.citation_interventions
            )
            refreshed.append(
                IndustryPolicyResult(
                    industry=policy.industry,
                    industry_label=policy.industry_label,
                    policy_code=policy.policy_code,
                    title=policy.title,
                    guidance=policy.guidance
                    + f" Learned from {len(group)} outcomes (success_rate={sr:.0%}).",
                    preferred_formats=preferred_formats,
                    preferred_sources=preferred_sources,
                    citation_interventions=interventions,
                    forbidden_universal_claims=NOT_UNIVERSAL_GEO,
                    sample_size=len(group),
                    success_rate=round(sr, 3),
                    active=True,
                )
            )
        else:
            refreshed.append(policy)

    industries_touched = sorted({r.industry for r in eligible})
    learning_questions = {
        "topics": "Which topics work?",
        "formats": "Which formats work?",
        "sources": "Which sources matter?",
        "writers": "Which writers succeed?",
        "citation_interventions": "Which interventions improve citation?",
        "industries": "Which industries behave differently?",
        "engines": "Which engines respond differently?",
    }
    summary = (
        f"Learning Engine 2.0 run over {len(eligible)} outcome-backed records; "
        f"{len(insights)} dimension insights; industries touched: "
        f"{', '.join(industries_touched) or 'none'}. {NOT_UNIVERSAL_GEO}"
    )
    return LearningRunResult(
        records_considered=len(eligible),
        insights=insights,
        industry_policies=refreshed,
        industries_touched=industries_touched,
        not_universal_geo_strategy=True,
        methodology_note=METHODOLOGY_NOTE,
        learning_questions=learning_questions,
        summary=summary,
    )


def catalog() -> dict[str, Any]:
    return {
        "industries": dict(INDUSTRY_LABELS),
        "industry_codes": list(INDUSTRIES),
        "learning_dimensions": list(LEARNING_DIMENSIONS),
        "loop_fields": [
            "Context",
            "Recommendation",
            "Expected Impact",
            "Confidence",
            "Execution",
            "Actual Outcome",
        ],
        "not_universal_geo_strategy": True,
        "not_universal_geo_note": NOT_UNIVERSAL_GEO,
        "methodology_note": METHODOLOGY_NOTE,
        "learning_questions": {
            "topics": "Which topics work?",
            "formats": "Which formats work?",
            "sources": "Which sources matter?",
            "writers": "Which writers succeed?",
            "citation_interventions": "Which interventions improve citation?",
            "industries": "Which industries behave differently?",
            "engines": "Which engines respond differently?",
        },
    }
