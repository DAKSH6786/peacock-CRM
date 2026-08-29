"""Generate realistic user queries across intent types for the AI Visibility scan.

Queries are template-built from the brand + real topic terms extracted from
the crawled site (never invented facts about the business) — the same
posture as the rest of Peacock One's evidence-first engines.
"""

from __future__ import annotations

from ai_visibility.models import GeneratedQuery


def build_queries(
    *,
    brand: str,
    topics: list[str],
    competitors: list[str] | None = None,
) -> list[GeneratedQuery]:
    competitors = competitors or []
    topic = topics[0] if topics else "this category"
    topic_clause = ", ".join(topics[:3]) if topics else "this category"
    competitor_clause = ", ".join(competitors[:2]) if competitors else "its main competitors"

    queries = [
        GeneratedQuery(
            intent="informational",
            query_text=f"What is {brand} and what does it offer for {topic_clause}?",
        ),
        GeneratedQuery(
            intent="informational",
            query_text=f"What should I know before choosing a provider for {topic_clause}?",
        ),
        GeneratedQuery(
            intent="comparison",
            query_text=f"How does {brand} compare to {competitor_clause} for {topic}?",
        ),
        GeneratedQuery(
            intent="comparison",
            query_text=f"What are the best alternatives to {brand} for {topic}?",
        ),
        GeneratedQuery(
            intent="purchase",
            query_text=f"Which {topic} provider should I buy from — {brand} or {competitor_clause}?",
        ),
        GeneratedQuery(
            intent="commercial",
            query_text=f"What do reviews say about {brand} for {topic_clause}?",
        ),
    ]
    return queries
