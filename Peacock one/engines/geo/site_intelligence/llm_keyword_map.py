"""LLM Keyword Map — terminology that recurs inside LLM answers, not Google keyword volume.

Built entirely from the already-collected ``geo_intelligence`` multi-LLM
extraction (real broadcast responses) cross-referenced against what the
crawled site's own pages actually contain.
"""

from __future__ import annotations

from geo_intelligence.extraction import tokenize
from geo_intelligence.gateway import ENGINE_META
from geo_intelligence.models import GeoExtractionResult, ProviderResponse

from site_intelligence.models import CompetitiveAssociationGap, LlmKeywordMap, LlmKeywordMapEntry


def build_llm_keyword_map(
    *,
    extraction: GeoExtractionResult,
    responses: list[ProviderResponse],
    site_text: str,
    client_brand: str,
    top_n: int = 20,
) -> LlmKeywordMap:
    engine_codes = sorted({r.engine_code for r in responses} | {c for k in extraction.keywords for c in k.engine_codes})
    site_tokens = set(tokenize(site_text))

    entries: list[LlmKeywordMapEntry] = []
    universal_terms: list[str] = []
    platform_specific_terms: dict[str, list[str]] = {code: [] for code in engine_codes}

    for keyword in extraction.keywords[:top_n]:
        per_engine_present = {code: code in keyword.engine_codes for code in engine_codes}
        already_on_site = any(word in site_tokens for word in keyword.phrase.split())
        if len(keyword.engine_codes) >= 3:
            universal_terms.append(keyword.phrase)
        elif len(keyword.engine_codes) == 1:
            platform_specific_terms.setdefault(keyword.engine_codes[0], []).append(keyword.phrase)

        opportunity = (
            "Already covered on your site — reinforce and keep fresh."
            if already_on_site
            else "Not found on your crawled pages — consider adding this term/topic."
        )
        entries.append(
            LlmKeywordMapEntry(term=keyword.phrase, per_engine_present=per_engine_present, opportunity=opportunity)
        )

    missing_semantic_entities = [
        e.name
        for e in extraction.entities
        if e.kind in {"competitor", "other"} and not any(word.lower() in site_tokens for word in e.name.split())
    ][:10]

    association_gaps: list[CompetitiveAssociationGap] = []
    for competitor in extraction.competitor_mentions:
        competitor_topics = sorted(
            {t.topic for t in extraction.top_brand_topics if t.associated_entity == competitor.name}
        )
        brand_topics = sorted(
            {t.topic for t in extraction.top_brand_topics if t.associated_entity == client_brand.strip().lower()}
        )
        missing = [t for t in competitor_topics if t not in brand_topics]
        if competitor_topics or missing:
            association_gaps.append(
                CompetitiveAssociationGap(
                    competitor=competitor.name,
                    competitor_topics=competitor_topics,
                    brand_topics=brand_topics,
                    missing_topics=missing,
                )
            )

    return LlmKeywordMap(
        entries=entries,
        universal_terms=sorted(set(universal_terms)),
        platform_specific_terms={
            ENGINE_META.get(code, {}).get("name", code): terms
            for code, terms in platform_specific_terms.items()
            if terms
        },
        missing_semantic_entities=missing_semantic_entities,
        competitive_association_gaps=association_gaps,
    )
