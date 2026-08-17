"""Deterministic AEO (Answer Engine Optimisation) page analysis."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any


QUESTION_RE = re.compile(
    r"\b(what|why|how|when|where|who|which|can|does|is|are|should)\b.+\?",
    re.IGNORECASE,
)
ENTITY_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b")


@dataclass(slots=True)
class PageAeoScore:
    url: str
    title: str | None
    answerability_score: float
    faq_coverage_score: float
    citation_readiness_score: float
    entity_coverage: float
    question_coverage: float
    questions_found: list[str] = field(default_factory=list)
    entities_found: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def analyse_page(page: dict[str, Any]) -> PageAeoScore:
    """Score a crawled page for answer-engine readiness (deterministic)."""
    url = str(page.get("url") or "")
    title = page.get("title")
    meta = page.get("meta_description") or ""
    h1 = _as_list(page.get("h1"))
    h2 = _as_list(page.get("h2"))
    h3 = _as_list(page.get("h3"))
    # CrawlPage stores heading fields as text (newline / JSON); normalise.
    if not h1 and isinstance(page.get("h1"), str) and page.get("h1"):
        h1 = [page["h1"]]
    if not h2 and isinstance(page.get("h2"), str) and page.get("h2"):
        h2 = [x for x in str(page["h2"]).split("\n") if x.strip()]
    if not h3 and isinstance(page.get("h3"), str) and page.get("h3"):
        h3 = [x for x in str(page["h3"]).split("\n") if x.strip()]
    body = page.get("body_text") or ""
    schema_blocks = _as_list(page.get("schema_blocks") or page.get("schema"))
    word_count = int(page.get("word_count") or len(str(body).split()))

    text_blob = " ".join(
        [
            str(title or ""),
            str(meta),
            " ".join(str(x) for x in h1 + h2 + h3),
            str(body)[:20000],
        ]
    )
    questions = list({m.group(0).strip() for m in QUESTION_RE.finditer(text_blob)})[:20]
    # FAQ schema boost
    faq_schema = False
    howto_schema = False
    qa_schema = False
    for block in schema_blocks:
        if not isinstance(block, dict):
            continue
        types = block.get("@type") or block.get("type") or ""
        type_s = json.dumps(types).lower()
        if "faq" in type_s:
            faq_schema = True
        if "howto" in type_s:
            howto_schema = True
        if "question" in type_s or "answer" in type_s:
            qa_schema = True

    heading_questions = sum(1 for h in h2 + h3 if "?" in str(h))
    faq_coverage = min(
        1.0,
        0.25 * (1 if faq_schema else 0)
        + 0.2 * (1 if qa_schema else 0)
        + 0.15 * (1 if howto_schema else 0)
        + 0.2 * min(1.0, heading_questions / 3.0)
        + 0.2 * min(1.0, len(questions) / 5.0),
    )

    # Answerability: direct answers near top, definitions, lists
    has_definition = bool(re.search(r"\bis\b.+\b(a|an|the)\b", text_blob[:1500], re.I))
    has_steps = bool(re.search(r"\b(step\s*1|first,|1\.)\b", text_blob[:3000], re.I))
    answerability = min(
        1.0,
        0.2 * (1 if title else 0)
        + 0.15 * (1 if meta and len(meta) >= 50 else 0)
        + 0.15 * (1 if h1 else 0)
        + 0.15 * min(1.0, word_count / 600.0)
        + 0.15 * (1 if has_definition else 0)
        + 0.1 * (1 if has_steps else 0)
        + 0.1 * faq_coverage,
    )

    # Citation readiness: canonical signals, outbound authority, schema, quotes
    outbound = _as_list(page.get("external_links"))
    has_quote = '"' in body or "“" in body
    citation_readiness = min(
        1.0,
        0.25 * (1 if schema_blocks else 0)
        + 0.2 * min(1.0, len(outbound) / 5.0)
        + 0.15 * (1 if has_quote else 0)
        + 0.15 * (1 if meta else 0)
        + 0.15 * min(1.0, word_count / 800.0)
        + 0.1 * (1 if page.get("canonical") else 0),
    )

    entities = []
    for m in ENTITY_RE.finditer(" ".join([str(title or ""), " ".join(str(x) for x in h1)])):
        name = m.group(1).strip()
        if len(name) > 2 and name.lower() not in {"the", "and", "for", "with"}:
            entities.append(name)
    entities = list(dict.fromkeys(entities))[:15]
    entity_coverage = min(1.0, len(entities) / 5.0)
    question_coverage = min(1.0, len(questions) / 5.0)

    recommendations: list[str] = []
    evidence: list[str] = []
    if not faq_schema and faq_coverage < 0.5:
        recommendations.append("Add FAQPage JSON-LD covering primary buyer questions")
        evidence.append("faq_schema_missing")
    if answerability < 0.55:
        recommendations.append("Add a concise definitional answer in the first 150 words")
        evidence.append(f"answerability={answerability:.2f}")
    if citation_readiness < 0.5:
        recommendations.append("Add authoritative outbound citations and quotable statements")
        evidence.append(f"citation_readiness={citation_readiness:.2f}")
    if entity_coverage < 0.4:
        recommendations.append("Strengthen named-entity coverage for brand, product, and topic entities")
        evidence.append(f"entities={len(entities)}")
    if not recommendations:
        recommendations.append("Maintain answer structure; expand entity and FAQ depth for contested queries")
        evidence.append("baseline_healthy")

    return PageAeoScore(
        url=url,
        title=str(title) if title else None,
        answerability_score=round(answerability * 100.0, 2),
        faq_coverage_score=round(faq_coverage * 100.0, 2),
        citation_readiness_score=round(citation_readiness * 100.0, 2),
        entity_coverage=round(entity_coverage * 100.0, 2),
        question_coverage=round(question_coverage * 100.0, 2),
        questions_found=questions,
        entities_found=entities,
        recommendations=recommendations,
        evidence=evidence,
    )


def aggregate_scores(pages: list[PageAeoScore]) -> dict[str, float]:
    if not pages:
        return {
            "answerability_score": 0.0,
            "faq_coverage_score": 0.0,
            "citation_readiness_score": 0.0,
            "entity_coverage": 0.0,
            "question_coverage": 0.0,
            "aeo_score": 0.0,
        }
    n = len(pages)
    ans = sum(p.answerability_score for p in pages) / n
    faq = sum(p.faq_coverage_score for p in pages) / n
    cite = sum(p.citation_readiness_score for p in pages) / n
    ent = sum(p.entity_coverage for p in pages) / n
    q = sum(p.question_coverage for p in pages) / n
    aeo = 0.3 * ans + 0.25 * faq + 0.25 * cite + 0.1 * ent + 0.1 * q
    return {
        "answerability_score": round(ans, 2),
        "faq_coverage_score": round(faq, 2),
        "citation_readiness_score": round(cite, 2),
        "entity_coverage": round(ent, 2),
        "question_coverage": round(q, 2),
        "aeo_score": round(aeo, 2),
    }
