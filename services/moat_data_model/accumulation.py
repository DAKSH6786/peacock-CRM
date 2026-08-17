"""Moat pathway accumulation — proprietary intelligence graph builders."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from db_models.moat_data_model import (
    EDGE_TYPES,
    METHODOLOGY_NOTE,
    MOAT_POSITIONING,
    NODE_KINDS,
    NODE_ROLES,
    NOT_UNIVERSAL_GEO,
    PATHWAY_KINDS,
    PATHWAY_LABELS,
)


@dataclass
class NodeSpec:
    node_role: str
    node_kind: str
    node_key: str
    label: str

    def validate(self) -> None:
        if self.node_role not in NODE_ROLES:
            raise ValueError(f"Unsupported node_role: {self.node_role}")
        if self.node_kind not in NODE_KINDS:
            raise ValueError(f"Unsupported node_kind: {self.node_kind}")


@dataclass
class EdgeSpec:
    from_ordinal: int
    to_ordinal: int
    edge_type: str
    weight: float = 1.0

    def validate(self) -> None:
        if self.edge_type not in EDGE_TYPES:
            raise ValueError(f"Unsupported edge_type: {self.edge_type}")


@dataclass
class OutcomeSpec:
    metric_key: str
    metric_value: float
    baseline_value: float | None = None
    delta: float | None = None
    observed_at: datetime | None = None
    provenance: str | None = None


@dataclass
class PathwaySpec:
    pathway_kind: str
    pathway_key: str
    nodes: list[NodeSpec]
    edges: list[EdgeSpec] = field(default_factory=list)
    outcomes: list[OutcomeSpec] = field(default_factory=list)
    industry: str | None = None
    topic_key: str | None = None
    expected_score: float | None = None
    actual_score: float | None = None
    outcome_delta: float | None = None
    confidence: float = 0.7
    sample_weight: float = 1.0
    source_system: str | None = None
    source_ref: str | None = None
    narrative: str = ""

    def validate(self) -> None:
        if self.pathway_kind not in PATHWAY_KINDS:
            raise ValueError(f"Unsupported pathway_kind: {self.pathway_kind}")
        if len(self.nodes) < 2:
            raise ValueError("pathway requires at least 2 nodes")
        for n in self.nodes:
            n.validate()
        for e in self.edges:
            e.validate()
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0–1")


@dataclass
class MoatRunSpec:
    client_brand: str
    industry: str | None = None
    pathways: list[PathwaySpec] = field(default_factory=list)
    analysed_at: datetime | None = None


@dataclass(slots=True)
class NodeResult:
    node_ordinal: int
    node_role: str
    node_kind: str
    node_key: str
    label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EdgeResult:
    from_ordinal: int
    to_ordinal: int
    edge_type: str
    weight: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class OutcomeResult:
    metric_key: str
    metric_value: float
    baseline_value: float | None
    delta: float | None
    observed_at: datetime
    provenance: str | None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["observed_at"] = self.observed_at.isoformat()
        return d


@dataclass(slots=True)
class PathwayResult:
    pathway_kind: str
    pathway_label: str
    pathway_key: str
    industry: str | None
    topic_key: str | None
    expected_score: float | None
    actual_score: float | None
    outcome_delta: float | None
    confidence: float
    sample_weight: float
    source_system: str | None
    source_ref: str | None
    narrative: str
    rank_order: int
    nodes: list[NodeResult]
    edges: list[EdgeResult]
    outcomes: list[OutcomeResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pathway_kind": self.pathway_kind,
            "pathway_label": self.pathway_label,
            "pathway_key": self.pathway_key,
            "industry": self.industry,
            "topic_key": self.topic_key,
            "expected_score": self.expected_score,
            "actual_score": self.actual_score,
            "outcome_delta": self.outcome_delta,
            "confidence": self.confidence,
            "sample_weight": self.sample_weight,
            "source_system": self.source_system,
            "source_ref": self.source_ref,
            "narrative": self.narrative,
            "rank_order": self.rank_order,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "outcomes": [o.to_dict() for o in self.outcomes],
            "chain": " → ".join(n.label for n in self.nodes),
        }


@dataclass
class MoatRunResult:
    client_brand: str
    industry: str | None
    pathways: list[PathwayResult]
    pathways_count: int
    nodes_count: int
    edges_count: int
    outcomes_count: int
    moat_strength_score: float
    mean_outcome_delta: float | None
    mean_confidence: float | None
    pathway_kind_coverage: list[str]
    moat_positioning: str
    methodology_note: str
    not_universal_geo: str
    summary: str
    analysed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "industry": self.industry,
            "pathways": [p.to_dict() for p in self.pathways],
            "pathways_count": self.pathways_count,
            "nodes_count": self.nodes_count,
            "edges_count": self.edges_count,
            "outcomes_count": self.outcomes_count,
            "moat_strength_score": self.moat_strength_score,
            "mean_outcome_delta": self.mean_outcome_delta,
            "mean_confidence": self.mean_confidence,
            "pathway_kind_coverage": self.pathway_kind_coverage,
            "moat_positioning": self.moat_positioning,
            "methodology_note": self.methodology_note,
            "not_universal_geo": self.not_universal_geo,
            "summary": self.summary,
            "analysed_at": self.analysed_at.isoformat(),
        }


def catalog() -> dict[str, Any]:
    return {
        "pathway_kinds": list(PATHWAY_KINDS),
        "pathway_labels": dict(PATHWAY_LABELS),
        "node_roles": list(NODE_ROLES),
        "node_kinds": list(NODE_KINDS),
        "edge_types": list(EDGE_TYPES),
        "moat_positioning": MOAT_POSITIONING,
        "not_universal_geo": NOT_UNIVERSAL_GEO,
        "methodology_note": METHODOLOGY_NOTE,
        "product_note": (
            "Peacock Moat Data Model is the proprietary intelligence accumulation "
            "layer — Peacock One's long-term competitive advantage."
        ),
        "example_pathways": [PATHWAY_LABELS[k] for k in PATHWAY_KINDS],
    }


def _chain(nodes: list[NodeSpec], edges: list[tuple[int, int, str]]) -> tuple[list[EdgeSpec], str]:
    edge_specs = [
        EdgeSpec(from_ordinal=a, to_ordinal=b, edge_type=t, weight=1.0) for a, b, t in edges
    ]
    narrative = " → ".join(n.label for n in nodes)
    return edge_specs, narrative


def demo_pathways(brand: str, industry: str | None = None) -> list[PathwaySpec]:
    ind = industry or "saas_b2b"
    now = datetime.now(tz=UTC)
    pathways: list[PathwaySpec] = []

    # 1. recommendation → outcome
    n1 = [
        NodeSpec("stimulus", "recommendation", "rec_compare_hubs", "Refresh /compare hubs"),
        NodeSpec("result", "outcome", "out_soa_lift", "SoA lift +7pp"),
    ]
    e1, narr1 = _chain(n1, [(0, 1, "leads_to")])
    pathways.append(
        PathwaySpec(
            pathway_kind="recommendation_outcome",
            pathway_key="rec_compare_hubs_soa",
            nodes=n1,
            edges=e1,
            outcomes=[
                OutcomeSpec("share_of_answer", 48.0, 41.0, 7.0, now - timedelta(days=2), "learning_engine2")
            ],
            industry=ind,
            expected_score=70.0,
            actual_score=78.0,
            outcome_delta=8.0,
            confidence=0.82,
            source_system="learning_engine2",
            narrative=f"{brand}: {narr1}",
        )
    )

    # 2. writer → topic → outcome
    n2 = [
        NodeSpec("stimulus", "writer", "writer_maya", "Writer Maya"),
        NodeSpec("mediator", "topic", "topic_benchmarks", "Topic: benchmarks"),
        NodeSpec("result", "outcome", "out_citability", "Citability +9"),
    ]
    e2, narr2 = _chain(n2, [(0, 1, "wrote"), (1, 2, "achieves")])
    pathways.append(
        PathwaySpec(
            pathway_kind="writer_topic_outcome",
            pathway_key="maya_benchmarks_citability",
            nodes=n2,
            edges=e2,
            outcomes=[
                OutcomeSpec("generative_citability_score", 64.0, 55.0, 9.0, now - timedelta(days=5), "writer_intelligence")
            ],
            industry=ind,
            topic_key="benchmarks",
            expected_score=72.0,
            actual_score=76.0,
            outcome_delta=4.0,
            confidence=0.79,
            source_system="writer_intelligence",
            narrative=f"{brand}: {narr2}",
        )
    )

    # 3. citation source → AI visibility
    n3 = [
        NodeSpec("stimulus", "citation_source", "src_reviewsite", "ReviewSite citations"),
        NodeSpec("result", "ai_visibility", "vis_ai", "AI Visibility +4.2"),
    ]
    e3, narr3 = _chain(n3, [(0, 1, "influences")])
    pathways.append(
        PathwaySpec(
            pathway_kind="citation_source_visibility",
            pathway_key="reviewsite_ai_vis",
            nodes=n3,
            edges=e3,
            outcomes=[
                OutcomeSpec("peacock_ai_visibility_score", 62.2, 58.0, 4.2, now - timedelta(days=3), "citation_graph")
            ],
            industry=ind,
            expected_score=65.0,
            actual_score=62.2,
            outcome_delta=4.2,
            confidence=0.74,
            source_system="citation_graph",
            narrative=f"{brand}: {narr3}",
        )
    )

    # 4. content structure → citation result
    n4 = [
        NodeSpec("intervention", "content_structure", "struct_faq_sources", "FAQ + source blocks"),
        NodeSpec("result", "citation_result", "cite_rate", "Citation rate +0.08"),
    ]
    e4, narr4 = _chain(n4, [(0, 1, "structures")])
    pathways.append(
        PathwaySpec(
            pathway_kind="content_structure_citation",
            pathway_key="faq_sources_citation",
            nodes=n4,
            edges=e4,
            outcomes=[
                OutcomeSpec("ai_citation_probability", 0.31, 0.23, 0.08, now - timedelta(days=4), "research_mode")
            ],
            industry=ind,
            expected_score=68.0,
            actual_score=71.0,
            outcome_delta=3.0,
            confidence=0.71,
            source_system="research_mode",
            narrative=f"{brand}: {narr4}",
        )
    )

    # 5. industry → GEO strategy → result
    n5 = [
        NodeSpec("stimulus", "industry", f"ind_{ind}", f"Industry: {ind}"),
        NodeSpec("intervention", "geo_strategy", "geo_compare_first", "Comparison-first GEO"),
        NodeSpec("result", "strategy_result", "geo_soa", "SoA recovery mid-single pp"),
    ]
    e5, narr5 = _chain(n5, [(0, 1, "applies_in"), (1, 2, "achieves")])
    pathways.append(
        PathwaySpec(
            pathway_kind="industry_geo_strategy_result",
            pathway_key=f"{ind}_compare_first_geo",
            nodes=n5,
            edges=e5,
            outcomes=[
                OutcomeSpec("share_of_answer", 46.0, 41.0, 5.0, now - timedelta(days=10), "learning_engine2")
            ],
            industry=ind,
            expected_score=66.0,
            actual_score=69.0,
            outcome_delta=5.0,
            confidence=0.68,
            source_system="learning_engine2",
            narrative=f"{brand}: {narr5}. Industry-scoped — not universal GEO.",
        )
    )

    # 6. entity gap → intervention → result
    n6 = [
        NodeSpec("stimulus", "entity_gap", "gap_reliability", "Entity gap: enterprise reliability"),
        NodeSpec("intervention", "intervention", "int_entity_pack", "Entity evidence pack"),
        NodeSpec("result", "outcome", "out_entity_auth", "Entity Authority +6"),
    ]
    e6, narr6 = _chain(n6, [(0, 1, "closes"), (1, 2, "realized")])
    pathways.append(
        PathwaySpec(
            pathway_kind="entity_gap_intervention_result",
            pathway_key="reliability_entity_pack",
            nodes=n6,
            edges=e6,
            outcomes=[
                OutcomeSpec("entity_authority_score", 69.0, 63.0, 6.0, now - timedelta(days=6), "entity_intelligence")
            ],
            industry=ind,
            expected_score=70.0,
            actual_score=73.0,
            outcome_delta=6.0,
            confidence=0.77,
            source_system="entity_intelligence",
            narrative=f"{brand}: {narr6}",
        )
    )

    # 7. competitor movement → response → outcome
    n7 = [
        NodeSpec("stimulus", "competitor_movement", "cm_cite_surge", "Competitor citation surge 18→31%"),
        NodeSpec("intervention", "response", "resp_benchmark", "Publish proprietary benchmark"),
        NodeSpec("result", "outcome", "out_threat_ease", "Competitive Threat −8"),
    ]
    e7, narr7 = _chain(n7, [(0, 1, "responds_to"), (1, 2, "realized")])
    pathways.append(
        PathwaySpec(
            pathway_kind="competitor_movement_response_outcome",
            pathway_key="cite_surge_benchmark_response",
            nodes=n7,
            edges=e7,
            outcomes=[
                OutcomeSpec("competitive_threat_score", 58.0, 66.0, -8.0, now - timedelta(days=1), "deep_competitor")
            ],
            industry=ind,
            expected_score=72.0,
            actual_score=75.0,
            outcome_delta=8.0,
            confidence=0.8,
            source_system="deep_competitor",
            narrative=f"{brand}: {narr7}",
        )
    )

    return pathways


def _moat_strength(pathways: list[PathwayResult]) -> float:
    if not pathways:
        return 0.0
    kinds = {p.pathway_kind for p in pathways}
    coverage = len(kinds) / max(len(PATHWAY_KINDS), 1)
    conf = sum(p.confidence * p.sample_weight for p in pathways) / sum(
        p.sample_weight for p in pathways
    )
    deltas = [abs(p.outcome_delta or 0.0) for p in pathways]
    delta_signal = min(1.0, (sum(deltas) / len(deltas)) / 10.0) if deltas else 0.0
    score = 100.0 * (0.40 * coverage + 0.35 * conf + 0.25 * delta_signal)
    return round(max(0.0, min(100.0, score)), 1)


def accumulate_moat(spec: MoatRunSpec) -> MoatRunResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")

    pathway_specs = list(spec.pathways) or demo_pathways(brand, spec.industry)
    for p in pathway_specs:
        p.validate()

    analysed_at = spec.analysed_at or datetime.now(tz=UTC)
    pathways: list[PathwayResult] = []
    for i, p in enumerate(pathway_specs):
        nodes = [
            NodeResult(
                node_ordinal=j,
                node_role=n.node_role,
                node_kind=n.node_kind,
                node_key=n.node_key,
                label=n.label,
            )
            for j, n in enumerate(p.nodes)
        ]
        # default sequential leads_to edges if none provided
        edges_in = list(p.edges)
        if not edges_in and len(nodes) >= 2:
            edges_in = [
                EdgeSpec(j, j + 1, "leads_to", 1.0) for j in range(len(nodes) - 1)
            ]
            for e in edges_in:
                e.validate()
        edges = [
            EdgeResult(
                from_ordinal=e.from_ordinal,
                to_ordinal=e.to_ordinal,
                edge_type=e.edge_type,
                weight=e.weight,
            )
            for e in edges_in
        ]
        outcomes = [
            OutcomeResult(
                metric_key=o.metric_key,
                metric_value=o.metric_value,
                baseline_value=o.baseline_value,
                delta=o.delta
                if o.delta is not None
                else (
                    None
                    if o.baseline_value is None
                    else round(o.metric_value - o.baseline_value, 4)
                ),
                observed_at=o.observed_at or analysed_at,
                provenance=o.provenance,
            )
            for o in p.outcomes
        ]
        pathways.append(
            PathwayResult(
                pathway_kind=p.pathway_kind,
                pathway_label=PATHWAY_LABELS[p.pathway_kind],
                pathway_key=p.pathway_key,
                industry=p.industry or spec.industry,
                topic_key=p.topic_key,
                expected_score=p.expected_score,
                actual_score=p.actual_score,
                outcome_delta=p.outcome_delta,
                confidence=round(p.confidence, 3),
                sample_weight=p.sample_weight,
                source_system=p.source_system,
                source_ref=p.source_ref,
                narrative=p.narrative or " → ".join(n.label for n in nodes),
                rank_order=i,
                nodes=nodes,
                edges=edges,
                outcomes=outcomes,
            )
        )

    nodes_count = sum(len(p.nodes) for p in pathways)
    edges_count = sum(len(p.edges) for p in pathways)
    outcomes_count = sum(len(p.outcomes) for p in pathways)
    deltas = [p.outcome_delta for p in pathways if p.outcome_delta is not None]
    mean_delta = round(sum(deltas) / len(deltas), 3) if deltas else None
    mean_conf = (
        round(sum(p.confidence for p in pathways) / len(pathways), 3) if pathways else None
    )
    coverage = sorted({p.pathway_kind for p in pathways})
    strength = _moat_strength(pathways)
    summary = (
        f"Moat run for {brand}: {len(pathways)} proprietary pathways "
        f"({len(coverage)}/{len(PATHWAY_KINDS)} kinds), strength {strength}. "
        f"{MOAT_POSITIONING}"
    )

    return MoatRunResult(
        client_brand=brand,
        industry=spec.industry,
        pathways=pathways,
        pathways_count=len(pathways),
        nodes_count=nodes_count,
        edges_count=edges_count,
        outcomes_count=outcomes_count,
        moat_strength_score=strength,
        mean_outcome_delta=mean_delta,
        mean_confidence=mean_conf,
        pathway_kind_coverage=coverage,
        moat_positioning=MOAT_POSITIONING,
        methodology_note=METHODOLOGY_NOTE,
        not_universal_geo=NOT_UNIVERSAL_GEO,
        summary=summary,
        analysed_at=analysed_at,
    )
