"""Content Creation Studio — CREATE WITH PEACOCK.

    Research -> Brief -> Outline -> Draft -> Sources -> FAQs -> Metadata ->
    Schema -> Internal Links -> CTA -> Optimization

Every section is template-generated from real inputs (the topic, real
entities/questions already extracted elsewhere, and the client's own crawled
pages for internal-link suggestions). Peacock never invents research,
statistics, quotations, citations, or sources — those sections are always
left as explicit placeholders for a human writer/expert to fill in.
"""

from __future__ import annotations

from content_intelligence.models import ContentBrief


def generate_content_brief(
    *,
    topic: str,
    brand: str,
    related_entities: list[str],
    related_questions: list[str],
    internal_link_candidates: list[str],
    content_type: str = "topic_cluster",
) -> ContentBrief:
    questions = related_questions[:5] or [
        f"What is {topic}?",
        f"How does {topic} work?",
        f"Why does {topic} matter for {brand}?",
    ]
    entities = related_entities[:5]

    research_notes = [
        f"[Add a verified fact about {topic} from a primary source here — Peacock does not invent research.]",
        f"[Add at least one original statistic or first-party data point about {topic}, with a citation.]",
        f"Related entities to weave in naturally: {', '.join(entities) or '(none detected — add manually)'}.",
    ]

    outline = [
        f"H1: {topic.title()}",
        "H2: What is it and why it matters",
        "H2: Key considerations",
    ]
    for q in questions:
        outline.append(f"H2 (question-phrased): {q}")
    outline.append("H2: How it compares / common alternatives")
    outline.append("H2: FAQs")

    draft_skeleton = "\n\n".join(
        [
            f"# {topic.title()}",
            f"[Write a 2-3 sentence direct-answer opening paragraph that plainly states what {topic} is, "
            "so it can be quoted verbatim by AI answer engines.]",
            "## Key considerations\n[Draft body content here — 400-600 words, citing real sources.]",
            "## FAQs\n" + "\n".join(f"**{q}**\n[Add a direct 1-2 sentence answer.]" for q in questions),
        ]
    )

    sources_needed = [
        "[Add a primary/authoritative outbound source relevant to this topic.]",
        "[Add an internal data point, survey, or expert quote if available — do not fabricate.]",
    ]

    faqs = [{"question": q, "answer": "[Add a direct, concise answer here.]"} for q in questions]

    suggested_title = f"{topic.title()} | {brand} Guide"[:65]
    suggested_meta_description = (
        f"Learn about {topic} — a practical overview covering key considerations, comparisons, "
        f"and frequently asked questions for {brand}."
    )[:160]
    suggested_schema = (
        '{\n  "@context": "https://schema.org",\n  "@type": "FAQPage",\n  "mainEntity": [\n'
        + ",\n".join(
            f'    {{"@type": "Question", "name": "{q}", "acceptedAnswer": '
            f'{{"@type": "Answer", "text": "[Add a direct answer here.]"}}}}'
            for q in questions[:3]
        )
        + "\n  ]\n}"
    )

    internal_links = [f"Link to: {u}" for u in internal_link_candidates[:5]] or [
        "[No related internal pages detected yet — add manually once more of the site is crawled.]"
    ]

    cta_suggestion = f"[Add a call to action relevant to {topic}, e.g. 'See how {brand} helps with {topic}.']"

    optimization_checklist = [
        "Direct answer in the first 1-2 sentences (Answerability)",
        "At least one original statistic or first-party data point (Evidence / Information Gain)",
        "FAQPage or QAPage schema markup (GEO — Technical AI Accessibility)",
        "Named entities relevant to the topic (Entity Authority)",
        "Outbound citation to an authoritative source (Citation Readiness)",
        "Single clear H1, logical H2 hierarchy (SEO — On-Page)",
        "Internal links to related pages (Internal Linking)",
        "Readable at a general-audience level (Readability)",
    ]

    return ContentBrief(
        topic=topic,
        research_notes=research_notes,
        outline=outline,
        draft_skeleton=draft_skeleton,
        sources_needed=sources_needed,
        faqs=faqs,
        suggested_title=suggested_title,
        suggested_meta_description=suggested_meta_description,
        suggested_schema=suggested_schema,
        internal_link_suggestions=internal_links,
        cta_suggestion=cta_suggestion,
        optimization_checklist=optimization_checklist,
        confidence="medium",
    )
