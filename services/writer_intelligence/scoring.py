"""Writer Intelligence 2.0 — DNA, Writer×Topic×Client outcome model, Outcome Graph.

Proprietary decision system. Does NOT use sample embedding similarity as the primary
recommendation signal.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any

from db_models.writer_intelligence import (
    METHODOLOGY_NOTE,
    PERFORMANCE_METRICS,
    SIMILARITY_ONLY_REJECTED,
    WRITER_DNA_TRAITS,
)


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9\-]{1,}", _norm(text)) if len(t) > 1}


def _overlap(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))


# Traits where higher raw score is worse for client outcome
_INVERTED_TRAITS = frozenset({"editing_effort"})

# Default weights for DNA composite (editing_effort inverted at combine time)
_DNA_WEIGHTS: dict[str, float] = {
    "subject_expertise": 0.09,
    "research_depth": 0.07,
    "technical_accuracy": 0.08,
    "style": 0.04,
    "tone": 0.04,
    "sentence_structure": 0.03,
    "readability": 0.05,
    "storytelling": 0.04,
    "citations": 0.06,
    "fact_density": 0.06,
    "original_thinking": 0.07,
    "seo_execution": 0.07,
    "aeo_execution": 0.07,
    "geo_execution": 0.07,
    "editing_effort": 0.05,
    "deadline_reliability": 0.06,
    "client_acceptance": 0.05,
}


@dataclass
class DnaTraitInput:
    trait_code: str
    score: float  # 0–100 (or 0–1 accepted and scaled)
    evidence: str | None = None

    def normalized_score(self) -> float:
        s = float(self.score)
        if s <= 1.0:
            s *= 100.0
        return _clamp100(s)


@dataclass
class WriterCandidate:
    writer_key: str
    display_name: str
    dna_traits: dict[str, float] = field(default_factory=dict)  # trait → 0–100
    dna_evidence: dict[str, str] = field(default_factory=dict)
    subject_tags: list[str] = field(default_factory=list)
    style_notes: str | None = None
    tone_notes: str | None = None
    prior_clients: list[str] = field(default_factory=list)
    prior_industries: list[str] = field(default_factory=list)
    prior_topics: list[str] = field(default_factory=list)
    prior_audiences: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "writer_key": self.writer_key,
            "display_name": self.display_name,
            "dna_traits": dict(self.dna_traits),
            "dna_evidence": dict(self.dna_evidence),
            "subject_tags": list(self.subject_tags),
            "style_notes": self.style_notes,
            "tone_notes": self.tone_notes,
            "prior_clients": list(self.prior_clients),
            "prior_industries": list(self.prior_industries),
            "prior_topics": list(self.prior_topics),
            "prior_audiences": list(self.prior_audiences),
        }


@dataclass
class ArticleOutcomeHistory:
    """Historical article on the Writer Outcome Graph."""

    article_key: str
    writer_key: str
    client_key: str
    industry: str
    topic: str
    audience: str | None = None
    title: str | None = None
    # Performance metrics (raw); revision_rounds lower=better
    approval: float | None = None  # 0–1
    revision_rounds: float | None = None
    ranking: float | None = None  # 0–1 higher better
    impressions: float | None = None
    ai_citations: float | None = None
    engagement: float | None = None
    links_earned: float | None = None
    conversion: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionContext:
    client_brand: str
    industry: str
    topic: str
    audience: str
    required_traits: list[str] = field(default_factory=list)
    preferred_tone: str | None = None
    needs_seo: bool = True
    needs_aeo: bool = True
    needs_geo: bool = True


@dataclass(slots=True)
class DnaTraitResult:
    trait_code: str
    score: float
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WriterDnaProfile:
    writer_key: str
    display_name: str
    traits: list[DnaTraitResult]
    dna_composite_score: float
    dna_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "writer_key": self.writer_key,
            "display_name": self.display_name,
            "traits": [t.to_dict() for t in self.traits],
            "dna_composite_score": self.dna_composite_score,
            "dna_summary": self.dna_summary,
        }


@dataclass(slots=True)
class OutcomeNode:
    node_kind: str
    node_key: str
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_kind": self.node_kind,
            "node_key": self.node_key,
            "label": self.label,
            "attributes": self.attributes,
        }


@dataclass(slots=True)
class OutcomeEdge:
    edge_type: str
    from_node_kind: str
    from_node_key: str
    to_node_kind: str
    to_node_key: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PerformanceRecordResult:
    article_key: str
    writer_key: str
    client_key: str
    industry: str
    topic: str
    metrics: dict[str, float | None]
    composite_outcome: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "article_key": self.article_key,
            "writer_key": self.writer_key,
            "client_key": self.client_key,
            "industry": self.industry,
            "topic": self.topic,
            "metrics": self.metrics,
            "composite_outcome": self.composite_outcome,
        }


@dataclass(slots=True)
class WriterRecommendationResult:
    writer_key: str
    display_name: str
    rank: int
    predicted_outcome_score: float
    dna_fit_score: float
    topic_fit_score: float
    client_fit_score: float
    audience_fit_score: float
    historical_outcome_score: float
    similarity_score_unused: float | None
    similarity_not_used_as_primary: bool
    rationale: str
    decision_answer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceResult:
    decision_question: str
    methodology_note: str
    similarity_only_rejected: bool
    similarity_rejection_note: str
    dna_profiles: list[WriterDnaProfile]
    recommendations: list[WriterRecommendationResult]
    outcome_nodes: list[OutcomeNode]
    outcome_edges: list[OutcomeEdge]
    performance_records: list[PerformanceRecordResult]
    top_writer_key: str | None
    top_outcome_score: float | None
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_question": self.decision_question,
            "methodology_note": self.methodology_note,
            "similarity_only_rejected": self.similarity_only_rejected,
            "similarity_rejection_note": self.similarity_rejection_note,
            "dna_profiles": [d.to_dict() for d in self.dna_profiles],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "outcome_nodes": [n.to_dict() for n in self.outcome_nodes],
            "outcome_edges": [e.to_dict() for e in self.outcome_edges],
            "performance_records": [p.to_dict() for p in self.performance_records],
            "top_writer_key": self.top_writer_key,
            "top_outcome_score": self.top_outcome_score,
            "summary": self.summary,
        }


def _scale_optional(value: float | None, *, typical_max: float) -> float | None:
    if value is None:
        return None
    if value <= 1.0 and typical_max > 1.0:
        # already normalized-ish for some metrics; keep impressions/links raw
        pass
    if typical_max <= 0:
        return _clamp01(value)
    return _clamp01(value / typical_max)


def composite_article_outcome(hist: ArticleOutcomeHistory) -> float:
    """Composite 0–100 outcome from performance metrics (revision_rounds inverted)."""
    parts: list[tuple[float, float]] = []
    if hist.approval is not None:
        parts.append((_clamp01(hist.approval) * 100.0, 0.18))
    if hist.revision_rounds is not None:
        # 0 rounds → 100, 5+ → ~0
        inv = _clamp100(100.0 - min(5.0, float(hist.revision_rounds)) * 20.0)
        parts.append((inv, 0.12))
    if hist.ranking is not None:
        parts.append((_clamp01(hist.ranking) * 100.0, 0.14))
    if hist.impressions is not None:
        parts.append((_clamp01(min(hist.impressions, 100_000) / 100_000) * 100.0, 0.10))
    if hist.ai_citations is not None:
        parts.append((_clamp01(min(hist.ai_citations, 50) / 50) * 100.0, 0.16))
    if hist.engagement is not None:
        eng = hist.engagement
        if eng > 1.0:
            eng = min(eng, 100.0) / 100.0
        parts.append((_clamp01(eng) * 100.0, 0.10))
    if hist.links_earned is not None:
        parts.append((_clamp01(min(hist.links_earned, 40) / 40) * 100.0, 0.10))
    if hist.conversion is not None:
        conv = hist.conversion
        if conv > 1.0:
            conv = min(conv, 100.0) / 100.0
        parts.append((_clamp01(conv) * 100.0, 0.10))

    if not parts:
        return 50.0
    total_w = sum(w for _, w in parts)
    return _clamp100(sum(v * w for v, w in parts) / total_w)


def build_writer_dna(writer: WriterCandidate) -> WriterDnaProfile:
    """Analyse Writer DNA across all proprietary traits."""
    traits: list[DnaTraitResult] = []
    trait_scores: dict[str, float] = {}

    for code in WRITER_DNA_TRAITS:
        raw = writer.dna_traits.get(code)
        if raw is None:
            # Soft priors from related tags
            if code == "subject_expertise" and writer.subject_tags:
                raw = min(90.0, 40.0 + 10.0 * len(writer.subject_tags))
            elif code == "tone" and writer.tone_notes:
                raw = 65.0
            elif code == "style" and writer.style_notes:
                raw = 65.0
            else:
                raw = 50.0  # neutral prior
        score = _clamp100(raw * 100.0 if raw <= 1.0 else raw)
        evidence = writer.dna_evidence.get(code) or (
            f"DNA trait «{code}» scored {score:.0f}/100"
            + (
                f" from subject tags {writer.subject_tags}"
                if code == "subject_expertise" and writer.subject_tags
                else " (observed / prior)."
            )
        )
        traits.append(DnaTraitResult(trait_code=code, score=score, evidence=evidence))
        trait_scores[code] = score

    composite = 0.0
    for code, weight in _DNA_WEIGHTS.items():
        s = trait_scores.get(code, 50.0)
        if code in _INVERTED_TRAITS:
            s = 100.0 - s
        composite += weight * s
    composite = _clamp100(composite)

    top = sorted(traits, key=lambda t: t.score, reverse=True)[:3]
    weak = sorted(
        [t for t in traits if t.trait_code not in _INVERTED_TRAITS],
        key=lambda t: t.score,
    )[:2]
    edit = next(t for t in traits if t.trait_code == "editing_effort")
    summary = (
        f"{writer.display_name} DNA composite {composite:.0f}/100. "
        f"Strengths: {', '.join(f'{t.trait_code}={t.score:.0f}' for t in top)}. "
        f"Watch: {', '.join(f'{t.trait_code}={t.score:.0f}' for t in weak)}; "
        f"editing_effort={edit.score:.0f}."
    )
    return WriterDnaProfile(
        writer_key=writer.writer_key,
        display_name=writer.display_name,
        traits=traits,
        dna_composite_score=composite,
        dna_summary=summary,
    )


def build_outcome_graph(
    history: list[ArticleOutcomeHistory],
    *,
    client_brand: str,
    industry: str,
    topic: str,
) -> tuple[list[OutcomeNode], list[OutcomeEdge], list[PerformanceRecordResult]]:
    """Build Writer → Article → Client → Industry → Topic → Performance graph."""
    nodes: dict[tuple[str, str], OutcomeNode] = {}
    edges: list[OutcomeEdge] = []
    records: list[PerformanceRecordResult] = []

    def add_node(kind: str, key: str, label: str, **attrs: Any) -> None:
        k = (kind, key)
        if k not in nodes:
            nodes[k] = OutcomeNode(
                node_kind=kind, node_key=key, label=label, attributes=attrs
            )

    # Context nodes for the decision
    add_node("client", _norm(client_brand) or "client", client_brand)
    add_node("industry", _norm(industry) or "industry", industry)
    add_node("topic", _norm(topic) or "topic", topic)

    for h in history:
        outcome = composite_article_outcome(h)
        writer_key = h.writer_key
        article_key = h.article_key
        client_key = h.client_key
        ind_key = _norm(h.industry) or "industry"
        topic_key = _norm(h.topic) or "topic"
        perf_key = f"perf:{article_key}"

        add_node("writer", writer_key, writer_key)
        add_node(
            "article",
            article_key,
            h.title or article_key,
            topic=h.topic,
            client=h.client_key,
        )
        add_node("client", _norm(client_key) or client_key, client_key)
        add_node("industry", ind_key, h.industry)
        add_node("topic", topic_key, h.topic)
        add_node(
            "performance",
            perf_key,
            f"Performance {article_key}",
            composite_outcome=outcome,
        )

        edges.append(
            OutcomeEdge("wrote", "writer", writer_key, "article", article_key, 1.0)
        )
        edges.append(
            OutcomeEdge(
                "for_client",
                "article",
                article_key,
                "client",
                _norm(client_key) or client_key,
                1.0,
            )
        )
        edges.append(
            OutcomeEdge(
                "in_industry",
                "article",
                article_key,
                "industry",
                ind_key,
                1.0,
            )
        )
        edges.append(
            OutcomeEdge("on_topic", "article", article_key, "topic", topic_key, 1.0)
        )
        edges.append(
            OutcomeEdge(
                "achieved",
                "article",
                article_key,
                "performance",
                perf_key,
                outcome / 100.0,
            )
        )

        metrics = {
            "approval": h.approval,
            "revision_rounds": h.revision_rounds,
            "ranking": h.ranking,
            "impressions": h.impressions,
            "ai_citations": h.ai_citations,
            "engagement": h.engagement,
            "links_earned": h.links_earned,
            "conversion": h.conversion,
        }
        records.append(
            PerformanceRecordResult(
                article_key=article_key,
                writer_key=writer_key,
                client_key=client_key,
                industry=h.industry,
                topic=h.topic,
                metrics=metrics,
                composite_outcome=outcome,
            )
        )

    return list(nodes.values()), edges, records


def _dna_fit_for_context(dna: WriterDnaProfile, ctx: DecisionContext) -> float:
    by = {t.trait_code: t.score for t in dna.traits}
    parts: list[tuple[float, float]] = [
        (by.get("subject_expertise", 50.0), 0.15),
        (by.get("research_depth", 50.0), 0.08),
        (by.get("technical_accuracy", 50.0), 0.10),
        (by.get("original_thinking", 50.0), 0.08),
        (by.get("citations", 50.0), 0.07),
        (by.get("fact_density", 50.0), 0.07),
        (by.get("readability", 50.0), 0.06),
        (by.get("storytelling", 50.0), 0.05),
        (100.0 - by.get("editing_effort", 50.0), 0.08),
        (by.get("deadline_reliability", 50.0), 0.08),
        (by.get("client_acceptance", 50.0), 0.08),
    ]
    if ctx.needs_seo:
        parts.append((by.get("seo_execution", 50.0), 0.10))
    if ctx.needs_aeo:
        parts.append((by.get("aeo_execution", 50.0), 0.10))
    if ctx.needs_geo:
        parts.append((by.get("geo_execution", 50.0), 0.10))
    for req in ctx.required_traits:
        if req in by:
            parts.append((by[req], 0.05))
    wsum = sum(w for _, w in parts)
    return _clamp100(sum(v * w for v, w in parts) / wsum)


def _topic_fit(writer: WriterCandidate, topic: str) -> float:
    blob = " ".join(writer.prior_topics + writer.subject_tags)
    base = _overlap(blob, topic) * 100.0
    if any(_norm(topic) in _norm(t) or _norm(t) in _norm(topic) for t in writer.prior_topics):
        base = max(base, 75.0)
    if any(_overlap(tag, topic) > 0.3 for tag in writer.subject_tags):
        base = max(base, 60.0)
    return _clamp100(base if base > 0 else 35.0)


def _client_fit(writer: WriterCandidate, client: str, industry: str) -> float:
    scores = []
    if writer.prior_clients:
        scores.append(
            max(_overlap(c, client) for c in writer.prior_clients) * 100.0
        )
        if any(_norm(c) == _norm(client) for c in writer.prior_clients):
            scores.append(90.0)
    if writer.prior_industries:
        scores.append(
            max(_overlap(i, industry) for i in writer.prior_industries) * 100.0
        )
        if any(_norm(i) == _norm(industry) for i in writer.prior_industries):
            scores.append(85.0)
    if not scores:
        return 45.0
    return _clamp100(mean(scores))


def _audience_fit(writer: WriterCandidate, audience: str, dna: WriterDnaProfile) -> float:
    by = {t.trait_code: t.score for t in dna.traits}
    hist = 0.0
    if writer.prior_audiences:
        hist = max(_overlap(a, audience) for a in writer.prior_audiences) * 100.0
    tone_boost = 0.0
    if writer.tone_notes and _overlap(writer.tone_notes, audience) > 0.1:
        tone_boost = 15.0
    readability = by.get("readability", 50.0)
    storytelling = by.get("storytelling", 50.0)
    return _clamp100(0.4 * (hist or 40.0) + 0.25 * readability + 0.2 * storytelling + tone_boost)


def _historical_outcome_for_writer(
    writer_key: str,
    records: list[PerformanceRecordResult],
    ctx: DecisionContext,
) -> float:
    mine = [r for r in records if r.writer_key == writer_key]
    if not mine:
        return 45.0
    # Weight outcomes closer to this topic/client/industry higher
    weighted: list[tuple[float, float]] = []
    for r in mine:
        w = 1.0
        w += 2.0 * _overlap(r.topic, ctx.topic)
        w += 2.0 * _overlap(r.client_key, ctx.client_brand)
        w += 1.5 * _overlap(r.industry, ctx.industry)
        weighted.append((r.composite_outcome, w))
    return _clamp100(sum(v * w for v, w in weighted) / sum(w for _, w in weighted))


def recommend_writers(
    *,
    context: DecisionContext,
    writers: list[WriterCandidate],
    history: list[ArticleOutcomeHistory],
) -> IntelligenceResult:
    """Core Writer×Topic×Client decision — predicted outcome, not sample similarity."""
    if not writers:
        raise ValueError("At least one writer candidate is required")
    if not context.client_brand.strip():
        raise ValueError("client_brand is required")
    if not context.topic.strip():
        raise ValueError("topic is required")
    if not context.audience.strip():
        raise ValueError("audience is required")

    decision_question = (
        f"Which writer is most likely to produce the best outcome for topic "
        f"«{context.topic}», client «{context.client_brand}», audience «{context.audience}»?"
    )

    dna_profiles = [build_writer_dna(w) for w in writers]
    dna_by_key = {d.writer_key: d for d in dna_profiles}
    writer_by_key = {w.writer_key: w for w in writers}

    nodes, edges, perf_records = build_outcome_graph(
        history,
        client_brand=context.client_brand,
        industry=context.industry,
        topic=context.topic,
    )

    scored: list[WriterRecommendationResult] = []
    for w in writers:
        dna = dna_by_key[w.writer_key]
        dna_fit = _dna_fit_for_context(dna, context)
        topic_fit = _topic_fit(w, context.topic)
        client_fit = _client_fit(w, context.client_brand, context.industry)
        audience_fit = _audience_fit(w, context.audience, dna)
        hist_out = _historical_outcome_for_writer(w.writer_key, perf_records, context)

        # Predicted outcome — proprietary blend; similarity deliberately unused
        predicted = _clamp100(
            0.28 * dna_fit
            + 0.22 * topic_fit
            + 0.18 * client_fit
            + 0.12 * audience_fit
            + 0.20 * hist_out
        )

        rationale = (
            f"Predicted outcome {predicted:.0f}/100 for {w.display_name} on "
            f"topic×client×audience — DNA fit {dna_fit:.0f}, topic {topic_fit:.0f}, "
            f"client/industry {client_fit:.0f}, audience {audience_fit:.0f}, "
            f"historical pathway {hist_out:.0f}. "
            f"Sample-similarity matching was not used as the primary signal."
        )
        decision_answer = (
            f"{w.display_name} is evaluated for best outcome on THIS topic "
            f"({context.topic}), THIS client ({context.client_brand}), and THIS audience "
            f"({context.audience}) — not for writing similarly to a reference sample."
        )
        scored.append(
            WriterRecommendationResult(
                writer_key=w.writer_key,
                display_name=w.display_name,
                rank=0,
                predicted_outcome_score=predicted,
                dna_fit_score=dna_fit,
                topic_fit_score=topic_fit,
                client_fit_score=client_fit,
                audience_fit_score=audience_fit,
                historical_outcome_score=hist_out,
                similarity_score_unused=None,
                similarity_not_used_as_primary=True,
                rationale=rationale,
                decision_answer=decision_answer,
            )
        )

    scored.sort(key=lambda r: r.predicted_outcome_score, reverse=True)
    for i, r in enumerate(scored, start=1):
        r.rank = i

    top = scored[0] if scored else None
    summary = (
        f"Writer Intelligence 2.0 ranked {len(scored)} writer(s). "
        + (
            f"Top: {top.display_name} (predicted outcome {top.predicted_outcome_score:.0f}/100). "
            if top
            else ""
        )
        + f"Decision question: {decision_question} "
        + SIMILARITY_ONLY_REJECTED
    )

    # Ensure PERFORMANCE_METRICS and json import used for attribute dumps if needed
    _ = PERFORMANCE_METRICS
    _ = json

    return IntelligenceResult(
        decision_question=decision_question,
        methodology_note=METHODOLOGY_NOTE,
        similarity_only_rejected=True,
        similarity_rejection_note=SIMILARITY_ONLY_REJECTED,
        dna_profiles=dna_profiles,
        recommendations=scored,
        outcome_nodes=nodes,
        outcome_edges=edges,
        performance_records=perf_records,
        top_writer_key=top.writer_key if top else None,
        top_outcome_score=top.predicted_outcome_score if top else None,
        summary=summary,
    )
