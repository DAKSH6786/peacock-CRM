"""Platform-specific GEO recommendations — framed as opportunities/signals, never guarantees."""

from __future__ import annotations

from geo_intelligence.models import GeoExtractionResult, PlatformRecommendation, ProviderResponse


def build_platform_recommendations(
    *,
    client_brand: str,
    responses: list[ProviderResponse],
    extraction: GeoExtractionResult,
) -> list[PlatformRecommendation]:
    terminology_by_engine = {t.engine_code: t for t in extraction.terminology_by_engine}
    recommendations: list[PlatformRecommendation] = []

    for response in responses:
        opportunities: list[str] = []
        term_profile = terminology_by_engine.get(response.engine_code)

        engine_questions = [q.question for q in extraction.questions if q.engine_code == response.engine_code]
        engine_citations = [c for c in extraction.citations if c.engine_code == response.engine_code]
        engine_competitors = [
            c.name for c in extraction.competitor_mentions if response.engine_code in c.engine_codes
        ]

        if term_profile and term_profile.top_terms:
            preferred = term_profile.top_terms[0]
            opportunities.append(
                f"{response.engine_name} tends to phrase this topic using \"{preferred}\" — "
                f"mirror that terminology in {client_brand}'s on-page copy and headings."
            )

        if engine_questions:
            opportunities.append(
                f"Answer directly and concisely: \"{engine_questions[0]}\" — add a quotable "
                f"FAQ-style answer block so {response.engine_name} can cite it verbatim."
            )

        if engine_citations:
            domains = ", ".join(sorted({c.domain for c in engine_citations})[:3])
            opportunities.append(
                f"{response.engine_name} drew on sources like {domains} — earn comparable "
                f"third-party coverage or publish original data that could replace them."
            )

        if extraction.missing_topics:
            opportunities.append(
                f"Cover the topic \"{extraction.missing_topics[0]}\" — {response.engine_name} "
                f"associates it with this space, but it isn't in {client_brand}'s current content."
            )

        if engine_competitors:
            opportunities.append(
                f"{response.engine_name} also mentions {', '.join(engine_competitors[:2])} — "
                f"differentiate with unique evidence, structured data, and direct comparisons."
            )

        if response.simulated:
            opportunities.append(
                f"{response.engine_name} plugin has no live API key configured, so this response is "
                "not from a live model call — connect the corresponding API key to get real signals."
            )

        if not opportunities:
            opportunities.append(
                f"No strong signals were extractable from {response.engine_name}'s response yet — "
                "broaden the research prompt or add more competitor/topic context and re-run."
            )

        strong_signals = sum(
            1
            for group in (engine_questions, engine_citations, engine_competitors)
            if group
        )
        if response.simulated:
            signal_strength = "low"
        elif strong_signals >= 2:
            signal_strength = "high"
        elif strong_signals == 1:
            signal_strength = "medium"
        else:
            signal_strength = "low"

        recommendations.append(
            PlatformRecommendation(
                engine_code=response.engine_code,
                engine_name=response.engine_name,
                platform_label=f"{response.engine_name} ({response.provider_code})",
                opportunities=opportunities,
                signal_strength=signal_strength,
            )
        )

    return recommendations
