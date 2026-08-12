"""Intelligent context selection — never dump the entire organisation database."""

from __future__ import annotations

from dataclasses import dataclass

from intelligence.models import (
    ContextBundle,
    ContextItem,
    RequestClassification,
    StrategicRequest,
    ThinkingDepth,
)
from intelligence.ports import ContextProvider

# Canonical context kinds the selector understands
CONTEXT_CATALOG: dict[str, str] = {
    "brand": "Brand identity and positioning",
    "products": "Product catalogue highlights",
    "services": "Service catalogue highlights",
    "locations": "Markets and locations",
    "audience": "Target audience summary",
    "personas": "Buyer / user personas",
    "business_model": "Business model notes",
    "conversion_objectives": "Conversion goals",
    "existing_content": "Existing content inventory snapshot",
    "website_architecture": "Website IA / key templates",
    "historical_performance": "Historical SEO / traffic performance",
    "competitors": "Competitor set snapshot",
    "writer_pool": "Available writers and skills",
    "previous_recommendations": "Prior recommendation outcomes",
    "crawl_summary": "Latest crawl summary",
    "seo_audit_summary": "Latest SEO audit summary",
}

DEFAULT_TOKEN_BUDGETS: dict[ThinkingDepth, int] = {
    ThinkingDepth.SHALLOW: 1_500,
    ThinkingDepth.STANDARD: 4_000,
    ThinkingDepth.DEEP: 8_000,
    ThinkingDepth.COUNCIL: 12_000,
}

# Intent → preferred context kinds (selection prior, not a full dump)
INTENT_CONTEXT_MAP: dict[str, list[str]] = {
    "seo_audit_review": ["seo_audit_summary", "crawl_summary", "website_architecture", "competitors", "previous_recommendations"],
    "content_strategy": ["existing_content", "audience", "personas", "products", "services", "writer_pool", "competitors"],
    "competitive_analysis": ["competitors", "brand", "products", "historical_performance"],
    "technical_fix": ["crawl_summary", "website_architecture", "seo_audit_summary"],
    "visibility_growth": ["brand", "competitors", "historical_performance", "existing_content", "conversion_objectives"],
    "execution_planning": ["previous_recommendations", "writer_pool", "conversion_objectives", "existing_content"],
    "general_strategy": ["brand", "business_model", "audience", "conversion_objectives", "competitors"],
}


@dataclass
class InMemoryContextProvider:
    """Test/local provider that exposes a bounded catalogue of fragments."""

    kind: str
    records: list[ContextItem]

    def candidates(self, request: StrategicRequest, classification: RequestClassification) -> list[ContextItem]:
        return list(self.records)


class ContextSelector:
    """Rank and budget context items; reject irrelevant kinds explicitly."""

    def __init__(
        self,
        providers: list[ContextProvider] | None = None,
        *,
        token_budget: int | None = None,
        max_items: int = 24,
    ) -> None:
        self.providers = providers or []
        self.token_budget = token_budget
        self.max_items = max_items

    def assemble(
        self,
        request: StrategicRequest,
        classification: RequestClassification,
    ) -> ContextBundle:
        budget = self.token_budget or DEFAULT_TOKEN_BUDGETS.get(
            classification.thinking_depth, 4000
        )
        preferred = list(
            dict.fromkeys(
                [
                    *classification.required_data,
                    *INTENT_CONTEXT_MAP.get(classification.user_intent, INTENT_CONTEXT_MAP["general_strategy"]),
                ]
            )
        )
        # Drop kinds not in catalogue
        preferred = [k for k in preferred if k in CONTEXT_CATALOG]

        candidates: list[ContextItem] = []
        available_kinds: set[str] = set()
        for provider in self.providers:
            available_kinds.add(provider.kind)
            if preferred and provider.kind not in preferred:
                # Still allow high-relevance providers if explicitly required later
                if provider.kind not in classification.required_data:
                    continue
            for item in provider.candidates(request, classification):
                # Boost items whose kind was requested
                boost = 0.15 if item.kind in preferred else 0.0
                candidates.append(
                    ContextItem(
                        kind=item.kind,
                        key=item.key,
                        summary=item.summary,
                        relevance=min(1.0, item.relevance + boost),
                        tokens_estimate=max(1, item.tokens_estimate),
                        source=item.source,
                        payload=item.payload,
                    )
                )

        candidates.sort(key=lambda c: (-c.relevance, c.tokens_estimate, c.kind, c.key))

        selected: list[ContextItem] = []
        tokens_used = 0
        selected_kinds: list[str] = []
        for item in candidates:
            if len(selected) >= self.max_items:
                break
            if tokens_used + item.tokens_estimate > budget:
                continue
            # Soft relevance floor — avoid noise
            if item.relevance < 0.35 and item.kind not in classification.required_data:
                continue
            selected.append(item)
            tokens_used += item.tokens_estimate
            if item.kind not in selected_kinds:
                selected_kinds.append(item.kind)

        rejected = [
            kind
            for kind in CONTEXT_CATALOG
            if kind not in selected_kinds
            and (kind in preferred or kind in available_kinds)
        ]
        rationale = [
            f"token_budget={budget}",
            f"preferred_kinds={preferred}",
            f"selected={len(selected)} items / {tokens_used} tokens",
            "Full-database dump forbidden — only relevance-ranked fragments included",
        ]
        if rejected:
            rationale.append(f"rejected_or_unused_kinds={rejected}")

        return ContextBundle(
            items=selected,
            selected_kinds=selected_kinds,
            rejected_kinds=rejected,
            token_budget=budget,
            tokens_used=tokens_used,
            selection_rationale=rationale,
        )


def default_demo_providers() -> list[ContextProvider]:
    """Bounded demo fragments for local/dev pipelines."""
    return [
        InMemoryContextProvider(
            "brand",
            [
                ContextItem("brand", "brand.primary", "Brand: Peacock One — generative visibility intelligence", 0.9, 40, "demo"),
            ],
        ),
        InMemoryContextProvider(
            "audience",
            [
                ContextItem("audience", "audience.primary", "Audience: enterprise SEO/AEO/GEO teams", 0.8, 30, "demo"),
            ],
        ),
        InMemoryContextProvider(
            "competitors",
            [
                ContextItem("competitors", "comp.set", "Competitors: traditional SEO suites and AI answer engines", 0.7, 35, "demo"),
            ],
        ),
        InMemoryContextProvider(
            "conversion_objectives",
            [
                ContextItem("conversion_objectives", "conv.demo", "Objective: qualified demo requests from marketing leaders", 0.75, 28, "demo"),
            ],
        ),
        InMemoryContextProvider(
            "writer_pool",
            [
                ContextItem("writer_pool", "writers.summary", "Writer pool available with SEO and technical content skills", 0.55, 25, "demo"),
            ],
        ),
        InMemoryContextProvider(
            "previous_recommendations",
            [
                ContextItem(
                    "previous_recommendations",
                    "recs.prior",
                    "Prior rec: fix orphan pages — partial completion",
                    0.6,
                    32,
                    "demo",
                    {"status": "partial"},
                ),
            ],
        ),
    ]
