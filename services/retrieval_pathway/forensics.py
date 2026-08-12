"""Retrieval Pathway forensics — estimated likelihoods from observed evidence.

Never claims access to proprietary AI ranking systems. Outputs use:
inferred retrieval pathway · observed evidence · estimated likelihood.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.retrieval_pathway import FORENSIC_CAUSES, METHODOLOGY_DISCLAIMER


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def likelihood_band(score: float) -> str:
    s = _clamp01(score)
    if s < 0.15:
        return "VERY_LOW"
    if s < 0.35:
        return "LOW"
    if s < 0.55:
        return "MEDIUM"
    if s < 0.75:
        return "HIGH"
    return "VERY_HIGH"


def uncertainty_band(*, evidence_confidence: float, signal_conflict: float) -> str:
    """Higher conflict / lower confidence → higher uncertainty."""
    raw = (1.0 - _clamp01(evidence_confidence)) * 0.6 + _clamp01(signal_conflict) * 0.4
    if raw < 0.25:
        return "low"
    if raw < 0.45:
        return "moderate"
    if raw < 0.7:
        return "high"
    return "very_high"


@dataclass
class ObservedEvidenceInput:
    """Structured observed evidence about the target page / query context."""

    # Availability / crawl
    page_reachable: bool | None = None
    http_status: int | None = None
    robots_blocked: bool | None = None
    noindex: bool | None = None
    # Relevance / entities
    topical_relevance: float | None = None  # 0–1 observed heuristic
    entity_relationship_strength: float | None = None
    # Competition / freshness
    competitor_page_strength: float | None = None
    source_freshness_days: int | None = None
    competitor_fresher: bool | None = None
    # Extractability / evidence quality
    extractability: float | None = None  # structured content, clarity
    supporting_evidence_strength: float | None = None
    third_party_corroboration: float | None = None
    # Outcome observations across generative answers
    content_appeared_retrieved: bool | None = None  # rough: URL/domain in answer context
    brand_mentioned: bool | None = None
    page_cited: bool | None = None
    citation_rate: float | None = None  # 0–1 across observations
    mention_rate: float | None = None
    # Meta
    observation_sample_size: int = 0
    evidence_confidence: float = 0.55  # overall trust in inputs


@dataclass(slots=True)
class CauseResult:
    cause_code: str
    estimated_likelihood: float
    likelihood_band: str
    uncertainty: str
    supporting_evidence: list[str]
    contrary_evidence: list[str]
    rationale: str
    is_primary: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BottleneckResult:
    bottleneck_stage: str
    headline: str
    retrieval_probability_band: str
    citation_selection_band: str
    estimated_retrieval_likelihood: float
    estimated_selection_likelihood: float
    interpretation: str
    recommended_investigation: str
    uncertainty: str
    disclaimer: str = METHODOLOGY_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ForensicReport:
    estimated_retrieval_likelihood: float
    estimated_selection_likelihood: float
    retrieval_likelihood_band: str
    selection_likelihood_band: str
    causes: list[CauseResult]
    bottleneck: BottleneckResult
    evidence_summary: list[dict[str, Any]] = field(default_factory=list)
    overall_uncertainty: str = "moderate"
    methodology: str = "inferred_retrieval_pathway"
    proprietary_ranking_access_claimed: bool = False
    disclaimer: str = METHODOLOGY_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _freshness_penalty(days: int | None) -> float:
    if days is None:
        return 0.35  # unknown → mild uncertainty contribution, not a hard fail
    if days <= 90:
        return 0.05
    if days <= 180:
        return 0.2
    if days <= 365:
        return 0.45
    if days <= 730:
        return 0.7
    return 0.9


def classify_causes(evidence: ObservedEvidenceInput) -> list[CauseResult]:
    """Estimate likelihood of each forensic cause from observed evidence."""
    conf = _clamp01(evidence.evidence_confidence)
    results: list[CauseResult] = []

    def add(
        code: str,
        likelihood: float,
        supporting: list[str],
        contrary: list[str],
        rationale: str,
        conflict: float = 0.0,
    ) -> None:
        unc = uncertainty_band(evidence_confidence=conf, signal_conflict=conflict)
        results.append(
            CauseResult(
                cause_code=code,
                estimated_likelihood=round(_clamp01(likelihood), 4),
                likelihood_band=likelihood_band(likelihood),
                uncertainty=unc,
                supporting_evidence=supporting,
                contrary_evidence=contrary,
                rationale=rationale,
            )
        )

    # page_unavailable
    unreachable = evidence.page_reachable is False or (
        evidence.http_status is not None and evidence.http_status >= 400
    )
    add(
        "page_unavailable",
        0.85 if unreachable else (0.1 if evidence.page_reachable else 0.35),
        supporting=(
            [f"Observed HTTP status={evidence.http_status}"]
            if unreachable
            else []
        )
        + (["page_reachable=false"] if evidence.page_reachable is False else []),
        contrary=["page_reachable=true"] if evidence.page_reachable is True else [],
        rationale=(
            "Observed evidence suggests the page may be unavailable to retrievers."
            if unreachable
            else "No strong observed unavailability signal; estimated likelihood remains low-to-moderate."
        ),
        conflict=0.2 if evidence.page_reachable is None else 0.05,
    )

    # crawl_restricted
    restricted = bool(evidence.robots_blocked or evidence.noindex)
    add(
        "crawl_restricted",
        0.8 if restricted else (0.15 if evidence.robots_blocked is False else 0.3),
        supporting=[
            *(["robots_blocked observed"] if evidence.robots_blocked else []),
            *(["noindex observed"] if evidence.noindex else []),
        ],
        contrary=["robots allow / indexable signals"] if evidence.robots_blocked is False else [],
        rationale=(
            "Observed crawl/index restrictions may limit the inferred retrieval pathway."
            if restricted
            else "No strong crawl-restriction evidence observed."
        ),
    )

    # weak_topical_relevance
    rel = evidence.topical_relevance
    weak_rel = 1.0 - rel if rel is not None else 0.4
    add(
        "weak_topical_relevance",
        weak_rel if rel is not None else 0.4,
        supporting=[f"observed topical_relevance={rel:.2f}"] if rel is not None else [],
        contrary=[f"topical_relevance={rel:.2f} is not weak"] if rel is not None and rel >= 0.6 else [],
        rationale=(
            "Observed topical relevance appears weak relative to the query cluster."
            if rel is not None and rel < 0.45
            else "Estimated from observed topical relevance; not a proprietary ranking score."
        ),
        conflict=0.35 if rel is None else 0.1,
    )

    # insufficient_entity_relationship
    ent = evidence.entity_relationship_strength
    add(
        "insufficient_entity_relationship",
        (1.0 - ent) if ent is not None else 0.4,
        supporting=[f"entity_relationship_strength={ent:.2f}"] if ent is not None else [],
        contrary=[] if ent is None or ent < 0.55 else [f"entity links look adequate ({ent:.2f})"],
        rationale="Observed entity-to-topic relationship strength informs this estimated likelihood.",
        conflict=0.35 if ent is None else 0.1,
    )

    # competitor_page_stronger
    comp = evidence.competitor_page_strength
    add(
        "competitor_page_stronger",
        comp if comp is not None else 0.45,
        supporting=[f"competitor_page_strength={comp:.2f}"] if comp is not None else [],
        contrary=[] if comp is None or comp >= 0.4 else ["competitors do not appear dominant"],
        rationale=(
            "Observed evidence suggests competing pages are substantially stronger "
            "candidates for citation selection."
            if comp is not None and comp >= 0.6
            else "Competitor strength estimated from observed comparative signals only."
        ),
        conflict=0.3 if comp is None else 0.1,
    )

    # source_freshness
    fresh_pen = _freshness_penalty(evidence.source_freshness_days)
    if evidence.competitor_fresher:
        fresh_pen = min(1.0, fresh_pen + 0.2)
    add(
        "source_freshness",
        fresh_pen,
        supporting=[
            *(
                [f"source_freshness_days={evidence.source_freshness_days}"]
                if evidence.source_freshness_days is not None
                else ["freshness unknown"]
            ),
            *(["competitor_fresher=true"] if evidence.competitor_fresher else []),
        ],
        contrary=["relatively fresh"] if fresh_pen < 0.25 else [],
        rationale="Estimated freshness disadvantage from observed publish/age signals.",
        conflict=0.4 if evidence.source_freshness_days is None else 0.1,
    )

    # poor_extractability
    ext = evidence.extractability
    add(
        "poor_extractability",
        (1.0 - ext) if ext is not None else 0.4,
        supporting=[f"extractability={ext:.2f}"] if ext is not None else [],
        contrary=[] if ext is None or ext < 0.55 else ["content appears extractable"],
        rationale="Observed extractability (structure, clarity, machine-readable cues) drives this estimate.",
        conflict=0.35 if ext is None else 0.1,
    )

    # insufficient_supporting_evidence
    sup = evidence.supporting_evidence_strength
    add(
        "insufficient_supporting_evidence",
        (1.0 - sup) if sup is not None else 0.4,
        supporting=[f"supporting_evidence_strength={sup:.2f}"] if sup is not None else [],
        contrary=[] if sup is None or sup < 0.55 else ["supporting evidence looks present"],
        rationale="Estimated from observed on-page supporting evidence density/quality.",
        conflict=0.35 if sup is None else 0.1,
    )

    # lack_of_third_party_corroboration
    corr = evidence.third_party_corroboration
    add(
        "lack_of_third_party_corroboration",
        (1.0 - corr) if corr is not None else 0.45,
        supporting=[f"third_party_corroboration={corr:.2f}"] if corr is not None else [],
        contrary=[] if corr is None or corr < 0.45 else ["third-party corroboration observed"],
        rationale="Estimated from observed third-party mentions/citations of the client page.",
        conflict=0.35 if corr is None else 0.1,
    )

    # content_not_retrieved
    not_retrieved = evidence.content_appeared_retrieved is False
    maybe = evidence.content_appeared_retrieved is None
    cite_r = evidence.citation_rate
    add(
        "content_not_retrieved",
        0.75
        if not_retrieved
        else (
            0.55
            if maybe and (cite_r is None or cite_r < 0.1)
            else (0.15 if evidence.content_appeared_retrieved else 0.35)
        ),
        supporting=[
            *(["content_appeared_retrieved=false"] if not_retrieved else []),
            *(
                [f"citation_rate={cite_r:.2f}"]
                if cite_r is not None and cite_r < 0.1
                else []
            ),
        ],
        contrary=(
            ["content_appeared_retrieved=true"]
            if evidence.content_appeared_retrieved
            else []
        ),
        rationale=(
            "Observed evidence is consistent with content not entering the inferred retrieval set."
            if not_retrieved
            else "Estimated retrieval absence from observed answer/citation patterns — not a vendor log."
        ),
        conflict=0.45 if maybe else 0.15,
    )

    # content_retrieved_but_not_selected
    retrieved = evidence.content_appeared_retrieved is True
    not_cited = evidence.page_cited is False or (
        cite_r is not None and cite_r < 0.15
    )
    retrieved_not_selected = retrieved and not_cited
    add(
        "content_retrieved_but_not_selected",
        0.82
        if retrieved_not_selected
        else (
            0.55
            if (evidence.topical_relevance or 0) >= 0.65
            and (cite_r is not None and cite_r < 0.2)
            else 0.2
        ),
        supporting=[
            *(["content_appeared_retrieved=true"] if retrieved else []),
            *(["page_cited=false"] if evidence.page_cited is False else []),
            *(
                [f"citation_rate={cite_r:.2f}"]
                if cite_r is not None
                else []
            ),
            *(
                [f"topical_relevance={evidence.topical_relevance:.2f}"]
                if evidence.topical_relevance is not None
                else []
            ),
        ],
        contrary=["page was cited in observed answers"] if evidence.page_cited else [],
        rationale=(
            "Observed evidence suggests the page may be retrieved or strongly relevant, "
            "yet citation selection favours other sources — an inferred pathway only."
            if retrieved_not_selected
            or (
                (evidence.topical_relevance or 0) >= 0.65
                and cite_r is not None
                and cite_r < 0.2
            )
            else "Limited observed support for a retrieve-but-not-select pattern."
        ),
        conflict=0.25,
    )

    # brand_mentioned_but_not_cited
    mentioned = evidence.brand_mentioned is True or (
        evidence.mention_rate is not None and evidence.mention_rate >= 0.2
    )
    cited = evidence.page_cited is True or (
        cite_r is not None and cite_r >= 0.2
    )
    add(
        "brand_mentioned_but_not_cited",
        0.8 if mentioned and not cited else (0.25 if mentioned else 0.15),
        supporting=[
            *(["brand_mentioned=true"] if evidence.brand_mentioned else []),
            *(
                [f"mention_rate={evidence.mention_rate:.2f}"]
                if evidence.mention_rate is not None
                else []
            ),
            *(["page_cited=false"] if evidence.page_cited is False else []),
        ],
        contrary=["page_cited=true"] if cited else [],
        rationale=(
            "Observed answers mention the brand without citing the target page."
            if mentioned and not cited
            else "Brand-mention-without-citation pattern not strongly observed."
        ),
    )

    # Ensure all causes present
    present = {r.cause_code for r in results}
    for code in FORENSIC_CAUSES:
        if code not in present:
            add(
                code,
                0.25,
                [],
                [],
                "Insufficient observed evidence; estimated likelihood near prior.",
                conflict=0.6,
            )

    results.sort(key=lambda r: r.estimated_likelihood, reverse=True)
    if results:
        results[0].is_primary = True
    return results


def estimate_pathway_likelihoods(
    evidence: ObservedEvidenceInput,
) -> tuple[float, float]:
    """Return (estimated_retrieval_likelihood, estimated_selection_likelihood)."""
    # Retrieval: availability + crawl + relevance + extractability + freshness
    avail = 0.2
    if evidence.page_reachable is True and not (
        evidence.http_status and evidence.http_status >= 400
    ):
        avail = 0.9
    elif evidence.page_reachable is False or (
        evidence.http_status and evidence.http_status >= 400
    ):
        avail = 0.05

    crawl = 0.5
    if evidence.robots_blocked or evidence.noindex:
        crawl = 0.1
    elif evidence.robots_blocked is False:
        crawl = 0.85

    rel = evidence.topical_relevance if evidence.topical_relevance is not None else 0.5
    ext = evidence.extractability if evidence.extractability is not None else 0.5
    fresh = 1.0 - _freshness_penalty(evidence.source_freshness_days)

    retrieval = (
        0.25 * avail
        + 0.2 * crawl
        + 0.3 * rel
        + 0.15 * ext
        + 0.1 * fresh
    )
    if evidence.content_appeared_retrieved is True:
        retrieval = max(retrieval, 0.7)
    elif evidence.content_appeared_retrieved is False:
        retrieval = min(retrieval, 0.35)
    if evidence.page_reachable is False or (
        evidence.http_status is not None and evidence.http_status >= 400
    ):
        retrieval = min(retrieval, 0.25)
    if evidence.robots_blocked or evidence.noindex:
        retrieval = min(retrieval, 0.4)

    # Selection: citation outcomes + corroboration + competitor gap + entity + support
    cite = evidence.citation_rate
    if cite is None:
        cite = 1.0 if evidence.page_cited else (0.05 if evidence.page_cited is False else 0.25)
    corr = (
        evidence.third_party_corroboration
        if evidence.third_party_corroboration is not None
        else 0.4
    )
    support = (
        evidence.supporting_evidence_strength
        if evidence.supporting_evidence_strength is not None
        else 0.4
    )
    ent = (
        evidence.entity_relationship_strength
        if evidence.entity_relationship_strength is not None
        else 0.4
    )
    comp = evidence.competitor_page_strength
    comp_gap = (1.0 - comp) if comp is not None else 0.45

    selection = (
        0.35 * cite
        + 0.15 * corr
        + 0.15 * support
        + 0.15 * ent
        + 0.2 * comp_gap
    )
    # If brand mentioned but not cited, selection stays low even if retrieval high
    if (evidence.brand_mentioned or (evidence.mention_rate or 0) >= 0.2) and (
        evidence.page_cited is False or (cite is not None and cite < 0.15)
    ):
        selection = min(selection, 0.3)

    return _clamp01(retrieval), _clamp01(selection)


def diagnose_bottleneck(
    *,
    retrieval: float,
    selection: float,
    causes: list[CauseResult],
    evidence: ObservedEvidenceInput,
) -> BottleneckResult:
    """Map estimated likelihoods to a headline bottleneck diagnosis."""
    r_band = likelihood_band(retrieval)
    s_band = likelihood_band(selection)
    primary = causes[0] if causes else None
    conf = _clamp01(evidence.evidence_confidence)
    conflict = 0.0
    if abs(retrieval - selection) < 0.1:
        conflict += 0.2
    if evidence.observation_sample_size < 5:
        conflict += 0.25
    unc = uncertainty_band(evidence_confidence=conf, signal_conflict=conflict)

    # Classic example: HIGH retrieval, LOW selection
    if retrieval >= 0.55 and selection < 0.4:
        stage = "selection"
        headline = "LIKELY VISIBILITY BOTTLENECK"
        interpretation = (
            "Your page appears strongly relevant on the inferred retrieval pathway, "
            "but competing sources are substantially more likely to be cited based on "
            "observed evidence. Estimated retrieval likelihood is "
            f"{r_band}; estimated citation selection likelihood is {s_band}."
        )
        investigation = "citation-quality gap"
    elif retrieval < 0.4 and selection < 0.4:
        if primary and primary.cause_code in {
            "page_unavailable",
            "crawl_restricted",
            "content_not_retrieved",
        }:
            stage = "retrieval"
            headline = "LIKELY RETRIEVAL BOTTLENECK"
            investigation = "availability and crawl access"
        else:
            stage = "retrieval"
            headline = "LIKELY RETRIEVAL BOTTLENECK"
            investigation = "topical relevance and retrieveability"
        interpretation = (
            "Observed evidence suggests the page may not consistently enter the "
            f"inferred retrieval pathway (estimated retrieval {r_band}; "
            f"estimated selection {s_band})."
        )
    elif retrieval >= 0.55 and selection >= 0.55:
        stage = "citation" if (evidence.citation_rate or 0) < 0.5 else "mixed"
        headline = "PATHWAY APPEARS COMPETITIVE"
        interpretation = (
            "Estimated retrieval and selection likelihoods are both relatively "
            f"favourable ({r_band} / {s_band}) from observed evidence. Residual gaps "
            "may reflect sample variance or unobserved factors."
        )
        investigation = "sample expansion and citation consistency"
    elif (
        (evidence.brand_mentioned or (evidence.mention_rate or 0) >= 0.2)
        and (evidence.page_cited is False or (evidence.citation_rate or 0) < 0.15)
    ):
        stage = "citation"
        headline = "BRAND MENTIONED WITHOUT CITATION"
        interpretation = (
            "Observed answers mention the brand, yet the target page is rarely cited. "
            "This is an inferred pathway pattern from observed evidence, not a vendor ranking dump."
        )
        investigation = "citation asset strength vs mention-only presence"
    else:
        stage = "unclear"
        headline = "MIXED / UNCERTAIN PATHWAY"
        interpretation = (
            f"Estimated retrieval={r_band}, selection={s_band}. Signals conflict or "
            "evidence is sparse; treat classifications as uncertain hypotheses."
        )
        investigation = "gather more observed evidence across engines"

    if primary and stage in {"selection", "retrieval"}:
        interpretation += (
            f" Leading hypothesized cause (estimated): {primary.cause_code.replace('_', ' ')} "
            f"({primary.likelihood_band}, uncertainty={primary.uncertainty})."
        )

    return BottleneckResult(
        bottleneck_stage=stage,
        headline=headline,
        retrieval_probability_band=r_band,
        citation_selection_band=s_band,
        estimated_retrieval_likelihood=round(retrieval, 4),
        estimated_selection_likelihood=round(selection, 4),
        interpretation=interpretation,
        recommended_investigation=investigation,
        uncertainty=unc,
    )


def run_forensics(evidence: ObservedEvidenceInput) -> ForensicReport:
    """Full inferred retrieval pathway forensic pass."""
    causes = classify_causes(evidence)
    retrieval, selection = estimate_pathway_likelihoods(evidence)
    bottleneck = diagnose_bottleneck(
        retrieval=retrieval,
        selection=selection,
        causes=causes,
        evidence=evidence,
    )
    evidence_summary = _summarise_evidence(evidence)
    overall = uncertainty_band(
        evidence_confidence=_clamp01(evidence.evidence_confidence),
        signal_conflict=0.3 if evidence.observation_sample_size < 5 else 0.1,
    )
    return ForensicReport(
        estimated_retrieval_likelihood=round(retrieval, 4),
        estimated_selection_likelihood=round(selection, 4),
        retrieval_likelihood_band=likelihood_band(retrieval),
        selection_likelihood_band=likelihood_band(selection),
        causes=causes,
        bottleneck=bottleneck,
        evidence_summary=evidence_summary,
        overall_uncertainty=overall,
    )


def _summarise_evidence(evidence: ObservedEvidenceInput) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    mapping = [
        ("page_reachable", evidence.page_reachable, "availability"),
        ("http_status", evidence.http_status, "availability"),
        ("robots_blocked", evidence.robots_blocked, "crawl"),
        ("noindex", evidence.noindex, "crawl"),
        ("topical_relevance", evidence.topical_relevance, "relevance"),
        ("entity_relationship_strength", evidence.entity_relationship_strength, "entities"),
        ("competitor_page_strength", evidence.competitor_page_strength, "competition"),
        ("source_freshness_days", evidence.source_freshness_days, "freshness"),
        ("extractability", evidence.extractability, "extractability"),
        ("supporting_evidence_strength", evidence.supporting_evidence_strength, "evidence"),
        ("third_party_corroboration", evidence.third_party_corroboration, "corroboration"),
        ("content_appeared_retrieved", evidence.content_appeared_retrieved, "retrieval"),
        ("brand_mentioned", evidence.brand_mentioned, "mention"),
        ("page_cited", evidence.page_cited, "citation"),
        ("citation_rate", evidence.citation_rate, "citation"),
        ("mention_rate", evidence.mention_rate, "mention"),
    ]
    for code, value, group in mapping:
        if value is None:
            continue
        items.append(
            {
                "evidence_code": code,
                "label": code.replace("_", " "),
                "observed_value": float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None,
                "observed_text": None if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value),
                "source": "observed",
                "group": group,
            }
        )
    return items


def causes_json(causes: list[CauseResult]) -> str:
    return json.dumps([c.to_dict() for c in causes], sort_keys=True)
