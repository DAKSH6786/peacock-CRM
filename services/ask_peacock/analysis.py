"""Ask Peacock 2.0 — intent routing + structured graph answers with evidence."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from db_models.ask_peacock import (
    ANSWER_SECTIONS,
    EXAMPLE_QUESTIONS,
    GRAPH_SURFACES,
    INTENT_LABELS,
    METHODOLOGY_NOTE,
    QUERY_INTENTS,
)


@dataclass
class GraphSignal:
    """A compact fact pulled from (or demoing) an intelligence-graph surface."""

    surface: str
    key: str
    value: str
    weight: float = 0.7
    ref_id: str | None = None

    def validate(self) -> None:
        if self.surface not in GRAPH_SURFACES:
            raise ValueError(f"Unsupported graph surface: {self.surface}")


@dataclass
class AskQuestionSpec:
    question: str


@dataclass
class AskSessionSpec:
    client_brand: str
    questions: list[str] = field(default_factory=list)
    # Optional live/demo graph signals; empty → demo_graph_signals()
    signals: list[GraphSignal] = field(default_factory=list)
    competitor_name: str | None = None
    budget_amount: str | None = None
    topic: str | None = None


@dataclass(slots=True)
class EvidenceItem:
    evidence_index: int
    graph_surface: str
    claim: str
    ref_id: str | None
    weight: float
    section: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StructuredAnswer:
    question_index: int
    question: str
    intent: str
    intent_label: str
    observed: str
    inferred: str
    recommended: str
    forecast: str
    confidence: float
    confidence_rationale: str
    graph_surfaces_used: list[str]
    answered_at: datetime
    evidence: list[EvidenceItem]

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_index": self.question_index,
            "question": self.question,
            "intent": self.intent,
            "intent_label": self.intent_label,
            "observed": self.observed,
            "inferred": self.inferred,
            "recommended": self.recommended,
            "forecast": self.forecast,
            "confidence": self.confidence,
            "confidence_rationale": self.confidence_rationale,
            "graph_surfaces_used": self.graph_surfaces_used,
            "answered_at": self.answered_at.isoformat(),
            "evidence": [e.to_dict() for e in self.evidence],
            "sections": {
                "OBSERVED": self.observed,
                "INFERRED": self.inferred,
                "RECOMMENDED": self.recommended,
                "FORECAST": self.forecast,
                "CONFIDENCE": self.confidence,
            },
        }


@dataclass
class AskSessionResult:
    client_brand: str
    answers: list[StructuredAnswer]
    questions_asked: int
    answers_produced: int
    evidence_items: int
    mean_confidence: float | None
    primary_intent: str | None
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "answers": [a.to_dict() for a in self.answers],
            "questions_asked": self.questions_asked,
            "answers_produced": self.answers_produced,
            "evidence_items": self.evidence_items,
            "mean_confidence": self.mean_confidence,
            "primary_intent": self.primary_intent,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
        }


def catalog() -> dict[str, Any]:
    return {
        "answer_sections": list(ANSWER_SECTIONS),
        "query_intents": list(QUERY_INTENTS),
        "intent_labels": dict(INTENT_LABELS),
        "example_questions": list(EXAMPLE_QUESTIONS),
        "graph_surfaces": list(GRAPH_SURFACES),
        "methodology_note": METHODOLOGY_NOTE,
        "structure_note": (
            "Every answer includes OBSERVED, INFERRED, RECOMMENDED, FORECAST, "
            "CONFIDENCE, plus evidence citations into intelligence-graph surfaces."
        ),
    }


def detect_intent(question: str) -> str:
    q = question.lower().strip()
    if (
        "beating us" in q
        or "beating me" in q
        or ("competitor" in q and ("why" in q or "ahead" in q or "winning" in q))
    ):
        return "competitor_beating_us"
    if (
        "lakh" in q
        or "90 day" in q
        or "90-day" in q
        or "next 90" in q
        or ("budget" in q and ("spend" in q or "allocate" in q or "do with" in q))
        or "₹" in question
        or "rs " in q
        or "inr" in q
    ):
        return "budget_allocation_90d"
    if (
        ("ten pages" in q or "10 pages" in q or "which pages" in q or "which ten" in q)
        and ("geo" in q or "generative" in q or "improvement" in q)
    ) or ("highest geo" in q or "geo improvement" in q):
        return "top_geo_pages"
    if "which writer" in q or ("writer" in q and ("topic" in q or "write" in q)):
        return "writer_for_topic"
    if "weakest" in q and (
        "engine" in q or "model" in q or "generative" in q or "llm" in q or "gpt" in q
    ):
        return "weakest_generative_engine"
    if (
        "external source" in q
        or "influencing ai" in q
        or ("sources" in q and ("opinion" in q or "ai" in q or "cit" in q))
        or "who cites" in q
    ):
        return "external_sources_influencing"
    if "what changed" in q or "this week" in q or "changed this" in q:
        return "what_changed_week"
    if "ceo" in q or "board" in q or "executive brief" in q or "c-suite" in q:
        return "ceo_brief"
    return "custom"


def _extract_competitor(question: str, fallback: str | None) -> str:
    if fallback:
        return fallback
    m = re.search(
        r"competitor\s+([A-Za-z0-9][A-Za-z0-9 &\-]{0,40})",
        question,
        flags=re.IGNORECASE,
    )
    if m:
        return m.group(1).strip().rstrip("?")
    return "Competitor A"


def _extract_budget(question: str, fallback: str | None) -> str:
    if fallback:
        return fallback
    m = re.search(r"(₹\s*[\d,.]+(?:\s*lakh)?|[\d,.]+\s*lakh|\$[\d,.]+)", question, re.I)
    if m:
        return m.group(1).strip()
    return "₹10 lakh"


def _extract_topic(question: str, fallback: str | None) -> str:
    if fallback:
        return fallback
    m = re.search(r"topic\s+([A-Za-z0-9][A-Za-z0-9 &\-]{0,60})", question, re.I)
    if m:
        return m.group(1).strip().rstrip("?")
    return "Topic X"


def demo_graph_signals(brand: str, competitor: str) -> list[GraphSignal]:
    """Compact demo slice of the intelligence graph for offline answers."""
    b = brand.strip() or "Brand"
    c = competitor.strip() or "Competitor A"
    return [
        GraphSignal(
            "deep_competitor",
            "share_gap",
            f"{c} leads {b} by +18pp share-of-answer on commercial prompts",
            0.9,
            "dc_share_gap",
        ),
        GraphSignal(
            "deep_competitor",
            "entity_coverage",
            f"{c} covers 14 entity facets vs {b}'s 7 on category hubs",
            0.85,
            "dc_entity",
        ),
        GraphSignal(
            "share_of_answer",
            "engine_split",
            "ChatGPT SoA 41%; Perplexity 28%; Gemini 22%; Claude 19%",
            0.8,
            "soa_engines",
        ),
        GraphSignal(
            "share_of_answer",
            "weakest_engine",
            "Claude is the weakest generative engine for brand presence (SoA 19%)",
            0.88,
            "soa_weak",
        ),
        GraphSignal(
            "citation_graph",
            "top_sources",
            "Industry wiki, ReviewSite, and ForumHub account for 62% of AI citations",
            0.86,
            "cg_top",
        ),
        GraphSignal(
            "citation_graph",
            "brand_mentions",
            f"{b} citations fell 23% week-over-week on commercial queries",
            0.82,
            "cg_drop",
        ),
        GraphSignal(
            "entity_intelligence",
            "association",
            f"{b} under-associated with 'enterprise reliability' vs {c}",
            0.78,
            "ei_assoc",
        ),
        GraphSignal(
            "opportunity_engine",
            "top_pages",
            "Top GEO pages: /pricing, /compare, /guides/roi, /integrations, "
            "/security, /case-studies, /api-docs, /blog/benchmarks, "
            "/solutions/smb, /glossary",
            0.84,
            "opp_pages",
        ),
        GraphSignal(
            "peacock90",
            "capacity",
            "90-day capacity supports ~12 content + 4 technical initiatives",
            0.8,
            "p90_cap",
        ),
        GraphSignal(
            "peacock90",
            "budget_split",
            "Prior plan: 45% content citability, 25% entity/schema, "
            "20% citation outreach, 10% measurement",
            0.83,
            "p90_budget",
        ),
        GraphSignal(
            "writer_intelligence",
            "best_writer",
            "Writer Maya (DNA: evidence-dense, comparison-native) best fit for Topic X",
            0.87,
            "wi_maya",
        ),
        GraphSignal(
            "writer_intelligence",
            "alt_writer",
            "Writer Arjun strong on narrative case studies; weaker on spec tables",
            0.7,
            "wi_arjun",
        ),
        GraphSignal(
            "temporal_intelligence",
            "week_delta",
            "This week: citation drop, competitor acceleration, Claude SoA dip",
            0.85,
            "ti_week",
        ),
        GraphSignal(
            "anomaly_engine",
            "top_anomaly",
            "Critical: AI visibility collapse (impact 91) + citation disappearance",
            0.9,
            "ae_top",
        ),
        GraphSignal(
            "revenue_attribution",
            "exposure",
            "Commercial prompt cluster ties to ~₹4.2L uncertain monthly pipeline",
            0.65,
            "ra_pipe",
        ),
        GraphSignal(
            "scenario_engine",
            "range",
            "Aggressive GEO push: SoA +6–11pp (p50) over 90 days if citability lands",
            0.6,
            "se_range",
        ),
        GraphSignal(
            "retrieval_pathway",
            "bottleneck",
            "Bottleneck: thin comparison pages fail answer-engine retrieval filters",
            0.77,
            "rp_bottle",
        ),
        GraphSignal(
            "geo_lab",
            "experiment",
            "FAQ+source block variant lifted citability +9% in lab (n small)",
            0.55,
            "gl_faq",
        ),
        GraphSignal(
            "judge2",
            "priority",
            "Judge priority: close comparison content gap before net-new blog volume",
            0.75,
            "j2_prio",
        ),
        GraphSignal(
            "learning_engine2",
            "policy",
            "Industry policy: comparison pages outperform thought-leadership for GEO",
            0.72,
            "le2_pol",
        ),
    ]


def _signals_by_surface(signals: list[GraphSignal]) -> dict[str, list[GraphSignal]]:
    out: dict[str, list[GraphSignal]] = {}
    for s in signals:
        out.setdefault(s.surface, []).append(s)
    return out


def _pick(signals: list[GraphSignal], *keys: str) -> list[GraphSignal]:
    wanted = set(keys)
    return [s for s in signals if s.key in wanted]


def _evidence_from(
    signals: list[GraphSignal],
    *,
    section: str,
    start_index: int = 0,
) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for i, s in enumerate(signals):
        items.append(
            EvidenceItem(
                evidence_index=start_index + i,
                graph_surface=s.surface,
                claim=s.value,
                ref_id=s.ref_id,
                weight=round(max(0.0, min(1.0, s.weight)), 3),
                section=section,
            )
        )
    return items


def _confidence(evidence: list[EvidenceItem], base: float) -> tuple[float, str]:
    if not evidence:
        return round(max(0.15, base * 0.4), 3), "Low coverage — few graph surfaces cited."
    weights = [e.weight for e in evidence]
    mean_w = sum(weights) / len(weights)
    surfaces = {e.graph_surface for e in evidence}
    coverage = min(1.0, len(surfaces) / 4.0)
    score = max(0.15, min(0.95, base * 0.45 + mean_w * 0.35 + coverage * 0.25))
    rationale = (
        f"Confidence {score:.2f} from {len(evidence)} evidence items across "
        f"{len(surfaces)} graph surfaces (mean weight {mean_w:.2f}). "
        "Not certainty — reflects evidence coverage and signal agreement."
    )
    return round(score, 3), rationale


def _answer_for_intent(
    *,
    intent: str,
    question: str,
    question_index: int,
    brand: str,
    competitor: str,
    budget: str,
    topic: str,
    signals: list[GraphSignal],
    now: datetime,
) -> StructuredAnswer:
    by = _signals_by_surface(signals)
    label = INTENT_LABELS.get(intent, INTENT_LABELS["custom"])

    if intent == "competitor_beating_us":
        used = _pick(
            signals,
            "share_gap",
            "entity_coverage",
            "bottleneck",
            "top_anomaly",
            "priority",
        )
        observed = (
            f"OBSERVED: {competitor} currently outpaces {brand} on generative "
            f"visibility — "
            f"{(by.get('deep_competitor') or [None])[0].value if by.get('deep_competitor') else 'share gap present'}; "
            f"comparison/retrieval pages remain thin."
        )
        inferred = (
            f"INFERRED: The gap is driven more by entity coverage and citability "
            f"on commercial prompts than by raw publishing volume. "
            f"{competitor}'s facet breadth compounds answer-engine selection."
        )
        recommended = (
            "RECOMMENDED: Prioritise comparison + entity-dense hubs, close the "
            "citability gap on commercial prompts, and challenge the top citation "
            "sources that currently amplify the competitor."
        )
        forecast = (
            "FORECAST: Closing the comparison/entity gap can recover a mid-single "
            "to low-double-digit SoA range over 90 days if citation outreach lands "
            "(scenario ranges, not point guarantees)."
        )
    elif intent == "budget_allocation_90d":
        used = _pick(signals, "budget_split", "capacity", "top_pages", "range", "exposure")
        observed = (
            f"OBSERVED: Available planning envelope is {budget} over ~90 days with "
            f"capacity for roughly a dozen content and a handful of technical "
            f"initiatives; commercial prompt clusters carry material pipeline exposure."
        )
        inferred = (
            "INFERRED: Spreading spend evenly across blog volume underperforms; "
            "industry learning and judge signals favour comparison/citability and "
            "entity work first."
        )
        recommended = (
            f"RECOMMENDED: Allocate {budget} roughly 45% citability content on top "
            f"GEO pages, 25% entity/schema, 20% citation outreach, 10% measurement — "
            f"and refuse volume that exceeds Peacock 90 capacity."
        )
        forecast = (
            "FORECAST: Expected SoA lift in the +6–11pp (p50) band if the citability "
            "programme executes; treat as a range with attribution uncertainty."
        )
    elif intent == "top_geo_pages":
        used = _pick(signals, "top_pages", "bottleneck", "experiment", "policy")
        pages = next((s.value for s in used if s.key == "top_pages"), "top commercial hubs")
        observed = f"OBSERVED: Opportunity Engine ranks highest-GEO pages as: {pages}."
        inferred = (
            "INFERRED: These pages sit on retrieval bottlenecks and commercial "
            "prompt clusters — lifting them compounds answer-engine selection more "
            "than net-new thought leadership."
        )
        recommended = (
            "RECOMMENDED: Ship evidence-dense refreshes (FAQ + source blocks, "
            "comparison tables) on the ten listed pages before expanding the "
            "publishing calendar."
        )
        forecast = (
            "FORECAST: Lab-like citability gains (~high-single-digit relative) are "
            "plausible on refreshed hubs; portfolio SoA impact depends on prompt coverage."
        )
    elif intent == "writer_for_topic":
        used = _pick(signals, "best_writer", "alt_writer", "policy")
        observed = (
            f"OBSERVED: Writer Intelligence maps {topic} to evidence-dense / "
            f"comparison-native DNA; Maya leads fit scores, Arjun is secondary for narrative."
        )
        inferred = (
            f"INFERRED: {topic} will be judged by answer engines on tables, sources, "
            "and entity clarity — narrative-only writers underperform here."
        )
        recommended = (
            f"RECOMMENDED: Assign Writer Maya to {topic}; pair with a citability "
            "checklist from Content Lab / GEO Lab variants."
        )
        forecast = (
            "FORECAST: Expected higher first-pass citability vs narrative-first assignment; "
            "outcome still depends on source quality and entity completeness."
        )
    elif intent == "weakest_generative_engine":
        used = _pick(signals, "weakest_engine", "engine_split", "week_delta", "brand_mentions")
        observed = (
            "OBSERVED: Share-of-answer split shows Claude as the weakest generative "
            "engine for brand presence, with recent week-over-week citation softness."
        )
        inferred = (
            "INFERRED: Weakness concentrates where retrieval pathways and citation "
            "sources under-serve that engine's preferred evidence patterns."
        )
        recommended = (
            "RECOMMENDED: Target Claude-oriented evidence packs (clear entities, "
            "quotable specs) on commercial hubs; re-probe SoA after citation outreach."
        )
        forecast = (
            "FORECAST: Engine-specific SoA can improve into the mid-20s band if "
            "citation and entity gaps close; other engines may move less."
        )
    elif intent == "external_sources_influencing":
        used = _pick(signals, "top_sources", "brand_mentions", "association", "share_gap")
        observed = (
            "OBSERVED: Citation Graph shows Industry wiki, ReviewSite, and ForumHub "
            "dominate AI citation share; brand mentions softened recently."
        )
        inferred = (
            "INFERRED: AI opinions about the brand are mediated by a small set of "
            "external amplifiers more than by owned blog volume."
        )
        recommended = (
            "RECOMMENDED: Prioritise correction/outreach on the top citation domains "
            "and publish entity-clear owned pages those sources can quote."
        )
        forecast = (
            "FORECAST: Shifting a few high-weight sources can move AI opinion "
            "faster than broad content velocity; expect lag of weeks, not days."
        )
    elif intent == "what_changed_week":
        used = _pick(signals, "week_delta", "top_anomaly", "brand_mentions", "share_gap")
        observed = (
            "OBSERVED: Temporal + Anomaly surfaces flag citation drop, competitor "
            "acceleration, and a Claude SoA dip this week."
        )
        inferred = (
            "INFERRED: The week’s movement is an unusual shift cluster, not routine "
            "noise — likely compounding into generative visibility pressure."
        )
        recommended = (
            "RECOMMENDED: Open an anomaly triage on citation disappearance and "
            "competitor acceleration; freeze low-ROI publishing until hubs are reinforced."
        )
        forecast = (
            "FORECAST: Without intervention, SoA pressure likely persists into the "
            "next measurement window; with hub+citation action, stabilisation is plausible."
        )
    elif intent == "ceo_brief":
        used = _pick(
            signals,
            "top_anomaly",
            "share_gap",
            "exposure",
            "budget_split",
            "range",
            "week_delta",
        )
        observed = (
            f"OBSERVED: {brand} faces a material generative-visibility gap vs "
            f"{competitor}, with critical anomaly pressure this week and uncertain "
            f"pipeline exposure on commercial prompts."
        )
        inferred = (
            "INFERRED: This is an executive-priority competitive and AI-visibility "
            "risk, not a routine SEO hygiene issue."
        )
        recommended = (
            f"RECOMMENDED: Approve a focused 90-day programme (citability + entity + "
            f"citation outreach) sized to capacity; insist on SoA/citation KPIs and "
            f"anomaly triage ownership."
        )
        forecast = (
            "FORECAST: Managed well, mid-single to low-double-digit SoA recovery "
            "range over 90 days; unmanaged, competitor lead likely widens."
        )
    else:
        used = signals[:5]
        observed = (
            f"OBSERVED: Ask Peacock scanned the intelligence graph for {brand} "
            f"against the question; top signals include competitor, citation, and "
            f"temporal/anomaly pressure."
        )
        inferred = (
            "INFERRED: The question maps to multiple graph surfaces; treat synthesis "
            "as directional until more specific intent filters apply."
        )
        recommended = (
            "RECOMMENDED: Reframe with a sharper ask (competitor, budget, pages, "
            "writer, engine, sources, weekly change, or CEO brief) for tighter routing."
        )
        forecast = (
            "FORECAST: More specific intents yield narrower forecast ranges and "
            "higher confidence from denser evidence."
        )

    # Evidence: OBSERVED from used signals; light INFERRED/RECOMMENDED tags
    evidence = _evidence_from(used, section="OBSERVED", start_index=0)
    if used:
        evidence.extend(
            _evidence_from(used[:2], section="INFERRED", start_index=len(evidence))
        )
        evidence.extend(
            _evidence_from(used[:2], section="RECOMMENDED", start_index=len(evidence))
        )
    # Ensure section labels exist even if reused claims
    for e in evidence:
        if e.section not in ANSWER_SECTIONS:
            e.section = "OBSERVED"

    conf, conf_rationale = _confidence(evidence, base=0.78 if intent != "custom" else 0.55)
    surfaces = sorted({e.graph_surface for e in evidence})

    return StructuredAnswer(
        question_index=question_index,
        question=question,
        intent=intent,
        intent_label=label,
        observed=observed,
        inferred=inferred,
        recommended=recommended,
        forecast=forecast,
        confidence=conf,
        confidence_rationale=conf_rationale,
        graph_surfaces_used=surfaces,
        answered_at=now,
        evidence=evidence,
    )


def answer_ask_session(spec: AskSessionSpec) -> AskSessionResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")

    questions = [q.strip() for q in spec.questions if q and q.strip()]
    if not questions:
        questions = list(EXAMPLE_QUESTIONS)

    competitor = _extract_competitor(questions[0], spec.competitor_name)
    budget = _extract_budget(
        next((q for q in questions if "lakh" in q.lower() or "₹" in q or "budget" in q.lower()), questions[0]),
        spec.budget_amount,
    )
    topic = _extract_topic(
        next((q for q in questions if "topic" in q.lower() or "writer" in q.lower()), questions[0]),
        spec.topic,
    )

    signals = list(spec.signals)
    for s in signals:
        s.validate()
    if not signals:
        signals = demo_graph_signals(brand, competitor)

    now = datetime.now(tz=UTC)
    answers: list[StructuredAnswer] = []
    for idx, q in enumerate(questions):
        intent = detect_intent(q)
        # Per-question entity extraction overrides
        c = _extract_competitor(q, competitor)
        bgt = _extract_budget(q, budget)
        top = _extract_topic(q, topic)
        answers.append(
            _answer_for_intent(
                intent=intent,
                question=q,
                question_index=idx,
                brand=brand,
                competitor=c,
                budget=bgt,
                topic=top,
                signals=signals,
                now=now,
            )
        )

    evidence_count = sum(len(a.evidence) for a in answers)
    mean_conf = (
        round(sum(a.confidence for a in answers) / len(answers), 3) if answers else None
    )
    # Primary intent = most common, else first
    intent_counts: dict[str, int] = {}
    for a in answers:
        intent_counts[a.intent] = intent_counts.get(a.intent, 0) + 1
    primary = (
        sorted(intent_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        if intent_counts
        else None
    )

    summary = (
        f"Ask Peacock 2.0 answered {len(answers)} question(s) for {brand} with "
        f"{evidence_count} evidence citations; mean confidence "
        f"{mean_conf if mean_conf is not None else 'n/a'}."
    )

    return AskSessionResult(
        client_brand=brand,
        answers=answers,
        questions_asked=len(questions),
        answers_produced=len(answers),
        evidence_items=evidence_count,
        mean_confidence=mean_conf,
        primary_intent=primary,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )
