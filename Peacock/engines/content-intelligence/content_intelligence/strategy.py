"""Content Strategy Engine — turn real gaps into concrete content-type recommendations."""

from __future__ import annotations

from content_intelligence.models import ContentRecommendation


def recommend_content_types(
    *,
    missing_topics: list[str],
    missing_entities: list[str],
    competitor_names: list[str],
    has_information_gain_gap: bool,
) -> list[ContentRecommendation]:
    recs: list[ContentRecommendation] = []

    if missing_topics:
        primary = missing_topics[0]
        recs.append(
            ContentRecommendation(
                content_type="pillar_page",
                title=f"{primary.title()}: The Complete Guide",
                rationale=f"'{primary}' is a topic AI platforms associate with this category but is not covered on the site.",
                target_topics=missing_topics[:5],
                priority="High",
            )
        )
        for topic in missing_topics[1:4]:
            recs.append(
                ContentRecommendation(
                    content_type="topic_cluster",
                    title=f"Supporting article: {topic.title()}",
                    rationale=f"Cluster content supporting the '{primary}' pillar page and covering '{topic}'.",
                    target_topics=[topic],
                    priority="Medium",
                )
            )

    if competitor_names:
        recs.append(
            ContentRecommendation(
                content_type="comparison_page",
                title=f"{competitor_names[0]} Alternatives — How to Choose",
                rationale=f"AI platforms mention {competitor_names[0]} alongside this brand — a direct comparison page can capture comparison-intent queries.",
                target_topics=competitor_names[:2],
                priority="High",
            )
        )

    if missing_entities:
        recs.append(
            ContentRecommendation(
                content_type="glossary_page",
                title="Glossary of Key Terms",
                rationale=f"Entities such as {', '.join(missing_entities[:3])} appear in AI/competitor content but are undefined on the site.",
                target_topics=missing_entities[:5],
                priority="Medium",
            )
        )

    recs.append(
        ContentRecommendation(
            content_type="faq_page",
            title="Frequently Asked Questions",
            rationale="Direct question-answer content improves AEO/GEO answerability and citation readiness.",
            target_topics=missing_topics[:3],
            priority="Medium",
        )
    )

    if has_information_gain_gap:
        recs.append(
            ContentRecommendation(
                content_type="research_content",
                title="Original Research / Benchmark Study",
                rationale="Competing/cited pages show stronger original-data signals — original research is the strongest lever for citation-worthiness.",
                target_topics=missing_topics[:2],
                priority="High",
            )
        )
        recs.append(
            ContentRecommendation(
                content_type="statistics_page",
                title="Industry Statistics & Data Hub",
                rationale="A dedicated, regularly-updated statistics page is a common source AI platforms cite for data-backed answers.",
                target_topics=missing_topics[:2],
                priority="Medium",
            )
        )
        recs.append(
            ContentRecommendation(
                content_type="case_study",
                title="Customer Case Study",
                rationale="First-party case studies provide original evidence that generic competitor content typically lacks.",
                target_topics=[],
                priority="Medium",
            )
        )

    recs.append(
        ContentRecommendation(
            content_type="thought_leadership",
            title="Expert Perspective / Opinion Piece",
            rationale="Authorial, expert-attributed content strengthens Brand Authority and E-E-A-T signals.",
            target_topics=[],
            priority="Low",
        )
    )
    recs.append(
        ContentRecommendation(
            content_type="commercial_content",
            title="Pricing / Plans Comparison",
            rationale="Purchase-intent queries observed in the AI Visibility scan benefit from clear commercial content.",
            target_topics=[],
            priority="Low",
        )
    )

    return recs
