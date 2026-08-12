"""Content Digital Twin simulation — evaluate article plans pre-publish."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.content_digital_twin import FINDING_CATEGORIES, SIMULATION_SURFACES


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9\-]{1,}", _norm(text)) if len(t) > 1}


def _contains_any(haystack: str, needles: list[str]) -> bool:
    h = _norm(haystack)
    return any(_norm(n) in h for n in needles if n and n.strip())


def _overlap_ratio(plan_blob: str, items: list[str]) -> tuple[float, list[str], list[str]]:
    """Return (coverage 0–1, matched, missing) for string items vs plan text."""
    if not items:
        return 1.0, [], []
    matched: list[str] = []
    missing: list[str] = []
    blob = _norm(plan_blob)
    plan_toks = _tokens(plan_blob)
    for item in items:
        item_n = _norm(item)
        item_toks = _tokens(item)
        # Match if phrase appears or majority of meaningful tokens overlap
        phrase_hit = bool(item_n) and item_n in blob
        tok_hit = bool(item_toks) and (len(item_toks & plan_toks) / max(1, len(item_toks))) >= 0.6
        if phrase_hit or tok_hit:
            matched.append(item)
        else:
            missing.append(item)
    return len(matched) / len(items), matched, missing


@dataclass
class ArticlePlan:
    """Mutable proposed article plan (user can edit and rerun)."""

    title: str
    slug: str
    outline_sections: list[str] = field(default_factory=list)
    target_keywords: list[str] = field(default_factory=list)
    covered_entities: list[str] = field(default_factory=list)
    evidence_claims: list[str] = field(default_factory=list)
    questions_answered: list[str] = field(default_factory=list)
    differentiation_angles: list[str] = field(default_factory=list)
    planned_citations: list[str] = field(default_factory=list)
    structured_elements: list[str] = field(default_factory=list)  # faq, table, definition…
    brand_voice_notes: str | None = None
    body_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArticlePlan:
        return cls(
            title=str(data.get("title") or ""),
            slug=str(data.get("slug") or ""),
            outline_sections=list(data.get("outline_sections") or []),
            target_keywords=list(data.get("target_keywords") or []),
            covered_entities=list(data.get("covered_entities") or []),
            evidence_claims=list(data.get("evidence_claims") or []),
            questions_answered=list(data.get("questions_answered") or []),
            differentiation_angles=list(data.get("differentiation_angles") or []),
            planned_citations=list(data.get("planned_citations") or []),
            structured_elements=list(data.get("structured_elements") or []),
            brand_voice_notes=data.get("brand_voice_notes"),
            body_summary=data.get("body_summary"),
        )

    def blob(self) -> str:
        parts = [
            self.title,
            self.slug,
            self.body_summary or "",
            self.brand_voice_notes or "",
            " ".join(self.outline_sections),
            " ".join(self.target_keywords),
            " ".join(self.covered_entities),
            " ".join(self.evidence_claims),
            " ".join(self.questions_answered),
            " ".join(self.differentiation_angles),
            " ".join(self.planned_citations),
            " ".join(self.structured_elements),
        ]
        return " ".join(parts)


@dataclass
class CompetitorPageRef:
    url: str
    title: str
    strengths: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    questions_covered: list[str] = field(default_factory=list)
    evidence_types: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompetitorPageRef:
        return cls(
            url=str(data.get("url") or ""),
            title=str(data.get("title") or ""),
            strengths=list(data.get("strengths") or []),
            entities=list(data.get("entities") or []),
            questions_covered=list(data.get("questions_covered") or []),
            evidence_types=list(data.get("evidence_types") or []),
        )


@dataclass
class PersonaRef:
    name: str
    intents: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PersonaRef:
        return cls(
            name=str(data.get("name") or ""),
            intents=list(data.get("intents") or []),
            questions=list(data.get("questions") or []),
        )


@dataclass
class AiAnswerScenario:
    prompt: str
    expected_answer_shape: str | None = None
    must_include_entities: list[str] = field(default_factory=list)
    must_answer_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AiAnswerScenario:
        return cls(
            prompt=str(data.get("prompt") or ""),
            expected_answer_shape=data.get("expected_answer_shape"),
            must_include_entities=list(data.get("must_include_entities") or []),
            must_answer_points=list(data.get("must_answer_points") or []),
        )


@dataclass
class BrandGuidelines:
    tone_keywords: list[str] = field(default_factory=list)
    required_mentions: list[str] = field(default_factory=list)
    forbidden_claims: list[str] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> BrandGuidelines:
        data = data or {}
        return cls(
            tone_keywords=list(data.get("tone_keywords") or []),
            required_mentions=list(data.get("required_mentions") or []),
            forbidden_claims=list(data.get("forbidden_claims") or []),
            rules=list(data.get("rules") or []),
        )


@dataclass
class SimulationContext:
    seo_requirements: list[str] = field(default_factory=list)
    aeo_requirements: list[str] = field(default_factory=list)
    geo_requirements: list[str] = field(default_factory=list)
    competitor_pages: list[CompetitorPageRef] = field(default_factory=list)
    target_entities: list[str] = field(default_factory=list)
    user_personas: list[PersonaRef] = field(default_factory=list)
    ai_answer_scenarios: list[AiAnswerScenario] = field(default_factory=list)
    citation_requirements: list[str] = field(default_factory=list)
    brand_guidelines: BrandGuidelines = field(default_factory=BrandGuidelines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seo_requirements": list(self.seo_requirements),
            "aeo_requirements": list(self.aeo_requirements),
            "geo_requirements": list(self.geo_requirements),
            "competitor_pages": [c.to_dict() for c in self.competitor_pages],
            "target_entities": list(self.target_entities),
            "user_personas": [p.to_dict() for p in self.user_personas],
            "ai_answer_scenarios": [a.to_dict() for a in self.ai_answer_scenarios],
            "citation_requirements": list(self.citation_requirements),
            "brand_guidelines": self.brand_guidelines.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimulationContext:
        return cls(
            seo_requirements=list(data.get("seo_requirements") or []),
            aeo_requirements=list(data.get("aeo_requirements") or []),
            geo_requirements=list(data.get("geo_requirements") or []),
            competitor_pages=[
                CompetitorPageRef.from_dict(x) for x in (data.get("competitor_pages") or [])
            ],
            target_entities=list(data.get("target_entities") or []),
            user_personas=[PersonaRef.from_dict(x) for x in (data.get("user_personas") or [])],
            ai_answer_scenarios=[
                AiAnswerScenario.from_dict(x) for x in (data.get("ai_answer_scenarios") or [])
            ],
            citation_requirements=list(data.get("citation_requirements") or []),
            brand_guidelines=BrandGuidelines.from_dict(data.get("brand_guidelines")),
        )


@dataclass(slots=True)
class RequirementScoreResult:
    surface: str
    coverage_score: float
    matched_count: int
    missing_count: int
    explanation: str
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FindingResult:
    category: str
    title: str
    detail: str
    severity: str = "info"
    related_surface: str | None = None
    related_item: str | None = None
    priority: float = 50.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TwinSimulationResult:
    predicted_strength_score: float
    readiness_score: float
    summary: str
    requirement_scores: list[RequirementScoreResult]
    findings: list[FindingResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicted_strength_score": self.predicted_strength_score,
            "readiness_score": self.readiness_score,
            "summary": self.summary,
            "requirement_scores": [r.to_dict() for r in self.requirement_scores],
            "findings": [f.to_dict() for f in self.findings],
        }


def _score_list_surface(
    surface: str,
    requirements: list[str],
    plan: ArticlePlan,
    *,
    extra_boost_if: list[str] | None = None,
) -> RequirementScoreResult:
    blob = plan.blob()
    cov, matched, missing = _overlap_ratio(blob, requirements)
    boost = 0.0
    if extra_boost_if:
        hits = sum(1 for e in extra_boost_if if _contains_any(blob, [e]))
        if extra_boost_if:
            boost = 0.1 * (hits / len(extra_boost_if))
    score = _clamp100(100.0 * min(1.0, cov + boost))
    return RequirementScoreResult(
        surface=surface,
        coverage_score=score,
        matched_count=len(matched),
        missing_count=len(missing),
        explanation=(
            f"Covered {len(matched)}/{len(requirements) or 0} {surface.replace('_', ' ')}; "
            f"missing {len(missing)}."
            if requirements
            else f"No explicit {surface.replace('_', ' ')} provided — scored as satisfied."
        ),
        matched=matched,
        missing=missing,
    )


def simulate_article_plan(
    plan: ArticlePlan,
    context: SimulationContext,
) -> TwinSimulationResult:
    """Simulate proposed article against all twin surfaces and emit findings."""
    if not plan.title.strip():
        raise ValueError("article plan title is required")

    findings: list[FindingResult] = []
    scores: list[RequirementScoreResult] = []
    blob = plan.blob()

    # --- SEO ---
    seo = _score_list_surface(
        "seo_requirements",
        context.seo_requirements or list(plan.target_keywords),
        plan,
        extra_boost_if=["h1", "meta", "internal link", "schema"],
    )
    # Keyword coverage bonus
    if plan.target_keywords:
        k_cov, _, k_miss = _overlap_ratio(blob, plan.target_keywords)
        seo.coverage_score = _clamp100(0.7 * seo.coverage_score + 30.0 * k_cov)
        for kw in k_miss:
            findings.append(
                FindingResult(
                    category="potential_weakness",
                    title=f"Target keyword underrepresented: {kw}",
                    detail="SEO simulation did not find this keyword in the outline or summary.",
                    severity="medium",
                    related_surface="seo_requirements",
                    related_item=kw,
                    priority=70.0,
                )
            )
    for item in seo.missing:
        findings.append(
            FindingResult(
                category="potential_weakness",
                title=f"SEO requirement gap: {item}",
                detail="Plan does not clearly address this SEO requirement.",
                severity="medium",
                related_surface="seo_requirements",
                related_item=item,
                priority=65.0,
            )
        )
    scores.append(seo)

    # --- AEO ---
    aeo_defaults = context.aeo_requirements or [
        "direct answer",
        "faq",
        "definition",
        "how to",
    ]
    aeo = _score_list_surface(
        "aeo_requirements",
        aeo_defaults if not context.aeo_requirements else context.aeo_requirements,
        plan,
        extra_boost_if=["faq", "definition", "direct answer", "schema faq"],
    )
    if not plan.questions_answered and not any(
        "faq" in _norm(e) for e in plan.structured_elements
    ):
        findings.append(
            FindingResult(
                category="missing_question",
                title="No explicit Q&A / FAQ planned",
                detail="AEO simulation expects answerable questions or FAQ structure.",
                severity="high",
                related_surface="aeo_requirements",
                priority=80.0,
            )
        )
        aeo.coverage_score = _clamp100(aeo.coverage_score * 0.7)
    for item in aeo.missing:
        findings.append(
            FindingResult(
                category="potential_weakness",
                title=f"AEO requirement gap: {item}",
                detail="Plan may underperform for answer engines without this element.",
                severity="medium",
                related_surface="aeo_requirements",
                related_item=item,
                priority=68.0,
            )
        )
    scores.append(aeo)

    # --- GEO ---
    geo_defaults = context.geo_requirements or [
        "entity clarity",
        "source attribution",
        "structured comparison",
        "fresh statistics",
    ]
    geo = _score_list_surface(
        "geo_requirements",
        geo_defaults if not context.geo_requirements else context.geo_requirements,
        plan,
        extra_boost_if=["comparison", "statistic", "citation", "entity", "table"],
    )
    if not plan.planned_citations and not plan.evidence_claims:
        findings.append(
            FindingResult(
                category="missing_evidence",
                title="Weak generative evidence footprint",
                detail="GEO simulation found few planned citations or evidence claims.",
                severity="high",
                related_surface="geo_requirements",
                priority=82.0,
            )
        )
        geo.coverage_score = _clamp100(geo.coverage_score * 0.75)
    for item in geo.missing:
        findings.append(
            FindingResult(
                category="potential_weakness",
                title=f"GEO requirement gap: {item}",
                detail="Plan may be less retrievable/citable in generative engines.",
                severity="medium",
                related_surface="geo_requirements",
                related_item=item,
                priority=66.0,
            )
        )
    scores.append(geo)

    # --- Target entities ---
    ent_cov, ent_matched, ent_missing = _overlap_ratio(
        " ".join(plan.covered_entities) + " " + blob, context.target_entities
    )
    entity_score = RequirementScoreResult(
        surface="target_entities",
        coverage_score=_clamp100(100.0 * ent_cov),
        matched_count=len(ent_matched),
        missing_count=len(ent_missing),
        explanation=(
            f"Plan covers {len(ent_matched)}/{len(context.target_entities) or 0} target entities."
            if context.target_entities
            else "No target entities provided — scored as satisfied."
        ),
        matched=ent_matched,
        missing=ent_missing,
    )
    for entity in ent_missing:
        findings.append(
            FindingResult(
                category="missing_entity",
                title=f"Missing entity: {entity}",
                detail="Target entity is not clearly represented in the article plan.",
                severity="high",
                related_surface="target_entities",
                related_item=entity,
                priority=85.0,
            )
        )
    scores.append(entity_score)

    # --- User personas ---
    persona_questions: list[str] = []
    for p in context.user_personas:
        persona_questions.extend(p.questions)
        persona_questions.extend(p.intents)
    p_cov, p_matched, p_missing = _overlap_ratio(
        " ".join(plan.questions_answered) + " " + blob, persona_questions
    )
    persona_score = RequirementScoreResult(
        surface="user_personas",
        coverage_score=_clamp100(100.0 * p_cov) if persona_questions else 100.0,
        matched_count=len(p_matched),
        missing_count=len(p_missing),
        explanation=(
            f"Addressed {len(p_matched)}/{len(persona_questions)} persona intents/questions."
            if persona_questions
            else "No personas provided — scored as satisfied."
        ),
        matched=p_matched,
        missing=p_missing,
    )
    for q in p_missing[:12]:
        findings.append(
            FindingResult(
                category="missing_question",
                title=f"Persona question uncovered: {q}",
                detail="User persona intent/question is not answered in the plan.",
                severity="medium",
                related_surface="user_personas",
                related_item=q,
                priority=72.0,
            )
        )
    scores.append(persona_score)

    # --- AI answer scenarios ---
    scenario_items: list[str] = []
    for s in context.ai_answer_scenarios:
        scenario_items.append(s.prompt)
        scenario_items.extend(s.must_answer_points)
        scenario_items.extend(s.must_include_entities)
    s_cov, s_matched, s_missing = _overlap_ratio(blob, scenario_items)
    # Prefer questions_answered + entities for AI scenarios
    ai_score = RequirementScoreResult(
        surface="ai_answer_scenarios",
        coverage_score=_clamp100(100.0 * s_cov) if scenario_items else 100.0,
        matched_count=len(s_matched),
        missing_count=len(s_missing),
        explanation=(
            f"Plan aligns with {len(s_matched)}/{len(scenario_items)} AI scenario elements."
            if scenario_items
            else "No AI answer scenarios provided — scored as satisfied."
        ),
        matched=s_matched,
        missing=s_missing,
    )
    for item in s_missing[:10]:
        findings.append(
            FindingResult(
                category="missing_question",
                title=f"AI scenario gap: {item}",
                detail="Article plan may not support this AI answer scenario.",
                severity="medium",
                related_surface="ai_answer_scenarios",
                related_item=item,
                priority=74.0,
            )
        )
    for s in context.ai_answer_scenarios:
        for ent in s.must_include_entities:
            if not _contains_any(" ".join(plan.covered_entities) + " " + blob, [ent]):
                findings.append(
                    FindingResult(
                        category="missing_entity",
                        title=f"AI scenario needs entity: {ent}",
                        detail=f"Scenario «{s.prompt[:80]}» expects this entity.",
                        severity="high",
                        related_surface="ai_answer_scenarios",
                        related_item=ent,
                        priority=86.0,
                    )
                )
    scores.append(ai_score)

    # --- Citation requirements ---
    cit_cov, cit_matched, cit_missing = _overlap_ratio(
        " ".join(plan.planned_citations) + " " + blob, context.citation_requirements
    )
    # Also reward having any planned citations / evidence
    base = cit_cov if context.citation_requirements else (
        1.0 if plan.planned_citations or plan.evidence_claims else 0.4
    )
    if plan.planned_citations:
        base = min(1.0, base + 0.15)
    citation_score = RequirementScoreResult(
        surface="citation_requirements",
        coverage_score=_clamp100(100.0 * base),
        matched_count=len(cit_matched),
        missing_count=len(cit_missing),
        explanation=(
            f"Satisfied {len(cit_matched)}/{len(context.citation_requirements) or 0} "
            f"citation requirements; {len(plan.planned_citations)} citations planned."
        ),
        matched=cit_matched,
        missing=cit_missing,
    )
    for item in cit_missing:
        findings.append(
            FindingResult(
                category="citation_opportunity",
                title=f"Add citation support: {item}",
                detail="Citation requirement is unmet — opportunity to earn quotable attribution.",
                severity="medium",
                related_surface="citation_requirements",
                related_item=item,
                priority=70.0,
            )
        )
    if plan.evidence_claims and not plan.planned_citations:
        findings.append(
            FindingResult(
                category="citation_opportunity",
                title="Claims without planned source attribution",
                detail="Evidence claims exist but few outbound/primary citations are planned.",
                severity="medium",
                related_surface="citation_requirements",
                priority=68.0,
            )
        )
    # Always surface at least one constructive citation opportunity when empty
    if not plan.planned_citations and not context.citation_requirements:
        findings.append(
            FindingResult(
                category="citation_opportunity",
                title="Plan primary-source citations",
                detail="Add attributable sources so generative systems can quote and retrieve.",
                severity="low",
                related_surface="citation_requirements",
                priority=55.0,
            )
        )
    scores.append(citation_score)

    # --- Brand guidelines ---
    bg = context.brand_guidelines
    brand_hits = 0
    brand_total = 0
    brand_missing: list[str] = []
    brand_matched: list[str] = []
    for mention in bg.required_mentions:
        brand_total += 1
        if _contains_any(blob, [mention]):
            brand_hits += 1
            brand_matched.append(mention)
        else:
            brand_missing.append(mention)
            findings.append(
                FindingResult(
                    category="potential_weakness",
                    title=f"Brand mention missing: {mention}",
                    detail="Required brand guideline mention not found in plan.",
                    severity="high",
                    related_surface="brand_guidelines",
                    related_item=mention,
                    priority=78.0,
                )
            )
    for claim in bg.forbidden_claims:
        if _contains_any(blob, [claim]):
            findings.append(
                FindingResult(
                    category="potential_weakness",
                    title=f"Forbidden claim risk: {claim}",
                    detail="Plan language may conflict with brand guidelines.",
                    severity="high",
                    related_surface="brand_guidelines",
                    related_item=claim,
                    priority=90.0,
                )
            )
            brand_total += 1  # penalty unit
    for tone in bg.tone_keywords:
        brand_total += 1
        if _contains_any((plan.brand_voice_notes or "") + " " + blob, [tone]):
            brand_hits += 1
            brand_matched.append(tone)
        else:
            brand_missing.append(f"tone:{tone}")
    brand_ratio = (brand_hits / brand_total) if brand_total else 1.0
    brand_score = RequirementScoreResult(
        surface="brand_guidelines",
        coverage_score=_clamp100(100.0 * brand_ratio),
        matched_count=len(brand_matched),
        missing_count=len(brand_missing),
        explanation=(
            f"Brand guideline alignment {brand_hits}/{brand_total or 0}."
            if brand_total
            else "No brand guidelines provided — scored as satisfied."
        ),
        matched=brand_matched,
        missing=brand_missing,
    )
    scores.append(brand_score)

    # --- Competitor pages ---
    competitor_gaps = 0
    competitor_checks = 0
    comp_matched: list[str] = []
    comp_missing: list[str] = []
    for page in context.competitor_pages:
        for strength in page.strengths:
            competitor_checks += 1
            if _contains_any(blob + " " + " ".join(plan.differentiation_angles), [strength]):
                comp_matched.append(f"{page.title}:{strength}")
            else:
                competitor_gaps += 1
                comp_missing.append(f"{page.title}:{strength}")
                findings.append(
                    FindingResult(
                        category="competitor_advantage",
                        title=f"Competitor advantage — {page.title}: {strength}",
                        detail=f"Rival page ({page.url or 'n/a'}) leads on this dimension.",
                        severity="medium",
                        related_surface="competitor_pages",
                        related_item=strength,
                        priority=76.0,
                    )
                )
        for q in page.questions_covered:
            if not _contains_any(" ".join(plan.questions_answered) + " " + blob, [q]):
                findings.append(
                    FindingResult(
                        category="missing_question",
                        title=f"Competitor covers question: {q}",
                        detail=f"{page.title} answers this; plan does not.",
                        severity="medium",
                        related_surface="competitor_pages",
                        related_item=q,
                        priority=73.0,
                    )
                )
        for ev in page.evidence_types:
            if not _contains_any(
                " ".join(plan.evidence_claims) + " " + " ".join(plan.structured_elements),
                [ev],
            ):
                findings.append(
                    FindingResult(
                        category="missing_evidence",
                        title=f"Competitor evidence type: {ev}",
                        detail=f"{page.title} includes {ev}; consider original evidence.",
                        severity="medium",
                        related_surface="competitor_pages",
                        related_item=ev,
                        priority=71.0,
                    )
                )
        for ent in page.entities:
            if not _contains_any(" ".join(plan.covered_entities) + " " + blob, [ent]):
                findings.append(
                    FindingResult(
                        category="missing_entity",
                        title=f"Competitor entity present: {ent}",
                        detail=f"{page.title} associates with {ent}; plan may lag entity coverage.",
                        severity="low",
                        related_surface="competitor_pages",
                        related_item=ent,
                        priority=60.0,
                    )
                )

    if competitor_checks:
        comp_cov = len(comp_matched) / competitor_checks
    else:
        comp_cov = 1.0
    # Differentiation improves competitor surface when angles exist
    if plan.differentiation_angles:
        comp_cov = min(1.0, comp_cov + 0.1 * min(1.0, len(plan.differentiation_angles) / 3))
        for angle in plan.differentiation_angles:
            findings.append(
                FindingResult(
                    category="differentiation_opportunity",
                    title=f"Differentiation angle: {angle}",
                    detail="Preserve and deepen this angle — competitors are weaker here.",
                    severity="info",
                    related_surface="competitor_pages",
                    related_item=angle,
                    priority=58.0,
                )
            )
    else:
        findings.append(
            FindingResult(
                category="differentiation_opportunity",
                title="Add a clear differentiation angle",
                detail="Without a unique angle, the twin risks mirroring competitor coverage.",
                severity="medium",
                related_surface="competitor_pages",
                priority=75.0,
            )
        )
    competitor_score = RequirementScoreResult(
        surface="competitor_pages",
        coverage_score=_clamp100(100.0 * comp_cov),
        matched_count=len(comp_matched),
        missing_count=len(comp_missing),
        explanation=(
            f"Matched {len(comp_matched)}/{competitor_checks or 0} competitor strength checks "
            f"across {len(context.competitor_pages)} rival pages."
            if context.competitor_pages
            else "No competitor pages provided — scored as satisfied."
        ),
        matched=comp_matched,
        missing=comp_missing,
    )
    scores.append(competitor_score)

    # --- Predicted strengths (positive findings) ---
    for rs in scores:
        if rs.coverage_score >= 70 and rs.matched:
            findings.append(
                FindingResult(
                    category="predicted_strength",
                    title=f"Strong {rs.surface.replace('_', ' ')} coverage",
                    detail=rs.explanation,
                    severity="info",
                    related_surface=rs.surface,
                    priority=40.0 + rs.coverage_score * 0.2,
                )
            )
    if plan.evidence_claims:
        findings.append(
            FindingResult(
                category="predicted_strength",
                title="Evidence claims planned",
                detail=f"{len(plan.evidence_claims)} evidence claim(s) in the plan.",
                severity="info",
                related_surface="geo_requirements",
                priority=55.0,
            )
        )
    if plan.structured_elements:
        findings.append(
            FindingResult(
                category="predicted_strength",
                title="Structured elements planned",
                detail="Includes: " + ", ".join(plan.structured_elements[:8]),
                severity="info",
                related_surface="aeo_requirements",
                priority=52.0,
            )
        )

    # Ensure category coverage for empty contexts with constructive defaults
    cats_present = {f.category for f in findings}
    if "predicted_strength" not in cats_present:
        findings.append(
            FindingResult(
                category="predicted_strength",
                title="Baseline plan structure present",
                detail=f"Title «{plan.title}» with {len(plan.outline_sections)} outline section(s).",
                severity="info",
                priority=35.0,
            )
        )
    if "differentiation_opportunity" not in cats_present:
        findings.append(
            FindingResult(
                category="differentiation_opportunity",
                title="Synthesize original comparison or framework",
                detail="Introduce a unique synthesis competitors cannot copy quickly.",
                severity="info",
                related_surface="competitor_pages",
                priority=50.0,
            )
        )

    # Composite scores
    by_surface = {s.surface: s.coverage_score for s in scores}
    weights = {
        "seo_requirements": 0.12,
        "aeo_requirements": 0.12,
        "geo_requirements": 0.12,
        "competitor_pages": 0.12,
        "target_entities": 0.12,
        "user_personas": 0.10,
        "ai_answer_scenarios": 0.12,
        "citation_requirements": 0.10,
        "brand_guidelines": 0.08,
    }
    predicted = sum(weights[k] * by_surface.get(k, 50.0) for k in weights)
    # Readiness penalizes high-severity gaps
    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")
    readiness = _clamp100(predicted - 4.0 * high - 1.5 * medium)

    # Sort findings: high severity first, then priority
    severity_rank = {"high": 0, "medium": 1, "low": 2, "info": 3}
    findings.sort(key=lambda f: (severity_rank.get(f.severity, 9), -f.priority))

    # Verify all surfaces scored
    assert set(s.surface for s in scores) == set(SIMULATION_SURFACES)

    weak_n = sum(1 for f in findings if f.category == "potential_weakness")
    miss_ent = sum(1 for f in findings if f.category == "missing_entity")
    summary = (
        f"Digital Twin «{plan.title}»: predicted strength {predicted:.0f}/100, "
        f"readiness {readiness:.0f}/100. "
        f"{weak_n} weakness signal(s), {miss_ent} missing entit(y/ies). "
        f"Modify the article plan and rerun evaluation to improve coverage."
    )

    # Ensure FINDING_CATEGORIES are known (used by API catalog)
    _ = FINDING_CATEGORIES

    return TwinSimulationResult(
        predicted_strength_score=_clamp100(predicted),
        readiness_score=readiness,
        summary=summary,
        requirement_scores=scores,
        findings=findings,
    )
