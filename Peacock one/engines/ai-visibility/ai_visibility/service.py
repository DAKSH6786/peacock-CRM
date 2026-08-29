"""Peacock AI Visibility Command Center — orchestrator.

Broadcasts realistic, intent-varied queries to every requested AI plugin via
the Peacock AI Gateway, and aggregates the real responses into a per-engine
and cross-engine (\"universal\") visibility report. A plugin with no live API
key never contributes a fabricated number — its engine report is marked
``available=False`` with a reason, exactly like ``site_intelligence.llm_geo_score``.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from geo_intelligence.gateway import DEFAULT_ENGINE_CODES, ENGINE_META, PeacockAIGateway
from llm_gateway.registry import LLMGateway

from ai_visibility.extraction import analyse_response
from ai_visibility.models import AiVisibilityCommandCenterReport, EngineVisibilityReport, QueryObservation
from ai_visibility.queries import build_queries


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


async def run_ai_visibility_scan(
    *,
    llm_gateway: LLMGateway | None,
    brand: str,
    topics: list[str],
    competitors: list[str] | None = None,
    client_domains: list[str] | None = None,
    competitor_domains: list[str] | None = None,
    engine_codes: list[str] | None = None,
    organisation_id: str = "ai-visibility",
) -> AiVisibilityCommandCenterReport:
    competitors = competitors or []
    codes = [c for c in (engine_codes or list(DEFAULT_ENGINE_CODES)) if c in ENGINE_META]
    queries = build_queries(brand=brand, topics=topics, competitors=competitors)

    gateway = PeacockAIGateway(llm_gateway)
    live_codes = gateway.available_engine_codes()

    observations_by_engine: dict[str, list[QueryObservation]] = defaultdict(list)

    for query in queries:
        responses = await gateway.broadcast(
            organisation_id=organisation_id,
            research_prompt=query.query_text,
            engine_codes=codes,
            simulated_responses={},  # never inject unrelated canned copy — see site_intelligence.report
        )
        for response in responses:
            observation = analyse_response(
                intent=query.intent,
                query_text=query.query_text,
                engine_code=response.engine_code,
                engine_name=response.engine_name,
                content=response.content,
                simulated=response.simulated,
                brand=brand,
                competitors=competitors,
                client_domains=client_domains,
                competitor_domains=competitor_domains,
            )
            observations_by_engine[response.engine_code].append(observation)

    engine_reports: list[EngineVisibilityReport] = []
    for code in codes:
        meta = ENGINE_META[code]
        observations = observations_by_engine.get(code, [])
        available = code in live_codes

        if not available:
            engine_reports.append(
                EngineVisibilityReport(
                    engine_code=code,
                    engine_name=meta["name"],
                    available=False,
                    reason_unavailable=(
                        f"{meta['name']} plugin has no live API key configured — no AI Visibility "
                        "signal was collected or estimated for this platform."
                    ),
                    observations=observations,
                )
            )
            continue

        n = len(observations) or 1
        mention_rate = sum(1 for o in observations if o.brand_mentioned) / n
        recommend_rate = sum(1 for o in observations if o.recommended) / n
        positions = [o.recommendation_position for o in observations if o.recommendation_position]
        avg_position = round(sum(positions) / len(positions), 2) if positions else None

        competitor_counter: Counter[str] = Counter()
        domain_counter: Counter[str] = Counter()
        attribute_counter: Counter[str] = Counter()
        sentiment_counter: Counter[str] = Counter()
        for o in observations:
            competitor_counter.update(o.competitor_mentions)
            domain_counter.update(o.cited_domains)
            attribute_counter.update(o.brand_attributes)
            if o.sentiment != "unknown":
                sentiment_counter[o.sentiment] += 1

        brand_total = sum(1 for o in observations if o.brand_mentioned)
        competitor_total = sum(competitor_counter.values())
        share_of_voice = (
            round(_clamp01(brand_total / (brand_total + competitor_total)), 3)
            if (brand_total + competitor_total) > 0
            else None
        )
        dominant_sentiment = sentiment_counter.most_common(1)[0][0] if sentiment_counter else "unknown"

        engine_reports.append(
            EngineVisibilityReport(
                engine_code=code,
                engine_name=meta["name"],
                available=True,
                reason_unavailable=None,
                observations=observations,
                brand_mention_rate=round(mention_rate, 3),
                recommendation_rate=round(recommend_rate, 3),
                average_recommendation_position=avg_position,
                ai_share_of_voice=share_of_voice,
                top_competitor_mentions=[c for c, _n in competitor_counter.most_common(5)],
                top_cited_domains=[d for d, _n in domain_counter.most_common(5)],
                top_brand_attributes=[a for a, _n in attribute_counter.most_common(5)],
                dominant_sentiment=dominant_sentiment,
            )
        )

    live_reports = [r for r in engine_reports if r.available]
    universal_share_of_answer = (
        round(sum(r.brand_mention_rate for r in live_reports) / len(live_reports), 3) if live_reports else None
    )
    voice_values = [r.ai_share_of_voice for r in live_reports if r.ai_share_of_voice is not None]
    universal_ai_share_of_voice = round(sum(voice_values) / len(voice_values), 3) if voice_values else None

    topic_visibility: dict[str, float] = {}
    if live_reports:
        by_intent: dict[str, list[bool]] = defaultdict(list)
        for report in live_reports:
            for o in report.observations:
                by_intent[o.intent].append(o.brand_mentioned)
        for intent, mentions in by_intent.items():
            topic_visibility[intent] = round(sum(1 for m in mentions if m) / len(mentions), 3) if mentions else 0.0

    return AiVisibilityCommandCenterReport(
        brand=brand,
        queries=queries,
        engine_reports=engine_reports,
        universal_share_of_answer=universal_share_of_answer,
        universal_ai_share_of_voice=universal_ai_share_of_voice,
        topic_visibility=topic_visibility,
    )
