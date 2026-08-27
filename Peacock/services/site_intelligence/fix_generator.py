"""Exact Fix Generator — concrete, non-published suggestions built from real page gaps.

Every draft is template-generated from data actually observed on the crawled
page (its own title/entities/keywords/questions) — never fabricated content
about the business. Peacock never auto-publishes anything; these are drafts
for a human to review.
"""

from __future__ import annotations

from crawler.store import StoredPage
from geo_intelligence.extraction import extract_title_case_entities, extract_questions, top_ngrams

from site_intelligence.models import CONFIDENCE_MEDIUM, ExactFix


def _top_keyword(page: StoredPage) -> str | None:
    ngrams = top_ngrams(page.body_text or "", sizes=(1, 2), top_k=5)
    return ngrams[0][0] if ngrams else None


def _primary_entity(page: StoredPage) -> str | None:
    entities = extract_title_case_entities(page.body_text or "")
    return entities[0] if entities else None


def fix_title(page: StoredPage) -> ExactFix:
    keyword = _top_keyword(page) or "your main topic"
    heading = (page.h1[0] if page.h1 else None) or page.title or keyword.title()
    draft = f"{heading[:45].strip()} | {keyword.title()} Guide"[:65]
    return ExactFix(
        fix_type="title",
        target_url=page.url,
        title="Suggested <title>",
        detail="Derived from the page's own H1/title and its top on-page keyword.",
        draft=draft,
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_meta_description(page: StoredPage) -> ExactFix:
    keyword = _top_keyword(page) or "this topic"
    heading = (page.h1[0] if page.h1 else None) or keyword.title()
    draft = (
        f"Learn about {heading} — a practical overview covering {keyword}, key benefits, "
        f"and what to consider before you decide."
    )[:160]
    return ExactFix(
        fix_type="meta_description",
        target_url=page.url,
        title="Suggested meta description",
        detail="Derived from the page's own H1 and top on-page keyword; keep it under 160 characters.",
        draft=draft,
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_h1(page: StoredPage) -> ExactFix:
    keyword = _top_keyword(page) or "Overview"
    draft = (page.title or keyword.title()).strip()
    return ExactFix(
        fix_type="heading",
        target_url=page.url,
        title="Suggested single H1",
        detail="Page has zero or multiple H1 tags — use exactly one that matches the page's primary topic.",
        draft=draft[:70],
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_faq(page: StoredPage, extra_questions: list[str] | None = None) -> ExactFix:
    questions = extract_questions(page.body_text or "")[:3]
    if extra_questions:
        questions = (questions + extra_questions)[:3]
    entity = _primary_entity(page) or "this topic"
    if not questions:
        questions = [
            f"What is {entity}?",
            f"How does {entity} work?",
            f"Why does {entity} matter?",
        ]
    draft_lines = [f"Q: {q}\nA: [Add a direct, 1-2 sentence answer here.]" for q in questions]
    return ExactFix(
        fix_type="faq",
        target_url=page.url,
        title="Suggested FAQ block",
        detail="Questions sourced from the page's own content (or a generic fallback) — draft the answers before publishing.",
        draft="\n\n".join(draft_lines),
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_schema(page: StoredPage) -> ExactFix:
    has_faq = any(str(b.get("@type", "")).lower() == "faqpage" for b in page.schema)
    if has_faq:
        return ExactFix(
            fix_type="schema",
            target_url=page.url,
            title="FAQPage schema already present",
            detail="No action needed — the page already declares FAQPage structured data.",
            draft="",
            confidence="high",
        )
    entity = _primary_entity(page) or (page.title or "This page")
    draft = (
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "FAQPage",\n'
        '  "mainEntity": [\n'
        '    {\n'
        '      "@type": "Question",\n'
        f'      "name": "What is {entity}?",\n'
        '      "acceptedAnswer": {\n'
        '        "@type": "Answer",\n'
        '        "text": "[Add a direct answer here.]"\n'
        '      }\n'
        '    }\n'
        '  ]\n'
        '}'
    )
    return ExactFix(
        fix_type="schema",
        target_url=page.url,
        title="Suggested FAQPage schema (JSON-LD)",
        detail="No FAQPage/QAPage schema.org block was found on this page.",
        draft=draft,
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_internal_link(page: StoredPage, *, orphan_target: str) -> ExactFix:
    anchor = _top_keyword(page) or "this page"
    return ExactFix(
        fix_type="internal_link",
        target_url=page.url,
        title="Suggested internal link",
        detail=f"{orphan_target} has no (or very few) inbound internal links from the crawled set.",
        draft=f'Add a contextual link from a related page using anchor text like "{anchor}" pointing to {orphan_target}.',
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_answer_paragraph(page: StoredPage, *, missing_topic: str) -> ExactFix:
    entity = _primary_entity(page) or (page.title or "this brand")
    draft = (
        f"[Add a 2-3 sentence direct-answer paragraph here that explicitly connects {entity} to "
        f'"{missing_topic}" — state the fact plainly in the first sentence so it can be quoted verbatim.]'
    )
    return ExactFix(
        fix_type="answer_paragraph",
        target_url=page.url,
        title=f"Suggested answer paragraph for '{missing_topic}'",
        detail="AI platforms associate this topic with the category, but it is not addressed on this page.",
        draft=draft,
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_missing_content_section(page: StoredPage, *, missing_topic: str) -> ExactFix:
    return ExactFix(
        fix_type="missing_content_section",
        target_url=page.url,
        title=f"Suggested new section: '{missing_topic.title()}'",
        detail="This topic appears in AI platform responses about the category but is absent from the page.",
        draft=f"## {missing_topic.title()}\n\n[Draft 2-3 paragraphs covering {missing_topic} with a concrete example or statistic.]",
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_entity_inclusion(page: StoredPage, *, entity: str) -> ExactFix:
    return ExactFix(
        fix_type="entity_inclusion",
        target_url=page.url,
        title=f"Mention entity: '{entity}'",
        detail="Competitors or AI answers associate this entity with the topic; the page does not mention it.",
        draft=f"[Add a sentence naming {entity} explicitly, with context on how it relates to this page's topic.]",
        confidence=CONFIDENCE_MEDIUM,
    )


def fix_citation_recommendation(page: StoredPage, *, domain: str) -> ExactFix:
    return ExactFix(
        fix_type="citation_recommendation",
        target_url=page.url,
        title=f"Cite or reference a source like '{domain}'",
        detail="AI platforms cite this type of source for this topic; this page has no comparable outbound citation.",
        draft=f"[Add an outbound link to a primary source comparable to {domain}, or publish original data that could replace it.]",
        confidence=CONFIDENCE_MEDIUM,
    )
