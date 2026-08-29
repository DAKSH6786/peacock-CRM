"""Peacock GEO Intelligence — the layer above the AI plugin connectors.

    AI Plugins -> Peacock AI Gateway -> Multi-LLM Response Collection ->
    Peacock GEO Intelligence Layer -> Keyword/Entity/Citation Extraction ->
    Platform-Specific GEO Recommendations -> Peacock One Dashboard

- ``gateway.PeacockAIGateway`` is the only place that broadcasts one prompt to
  every selected AI plugin (ChatGPT/OpenAI, Gemini, Claude/Anthropic,
  Perplexity, DeepSeek). It never imports a provider SDK directly — plugins
  are ``llm_gateway`` adapters, registered only from environment variables.
- ``extraction`` turns collected plugin responses into keyword, entity,
  question, citation, competitor, and terminology signals.
- ``recommendations`` turns those signals into platform-specific GEO
  opportunities — explicitly not a guaranteed-ranking claim.
- ``service.run_geo_intelligence`` runs the full pipeline end to end.
"""

from geo_intelligence.demo_content import default_simulated_responses
from geo_intelligence.extraction import extract_geo_intelligence
from geo_intelligence.gateway import DEFAULT_ENGINE_CODES, ENGINE_META, PeacockAIGateway
from geo_intelligence.models import (
    GEO_DISCLAIMER,
    METHODOLOGY_NOTE,
    CitationSignal,
    EntityMention,
    GeoExtractionResult,
    GeoIntelligenceReport,
    KeywordSignal,
    PlatformRecommendation,
    ProviderResponse,
    QuestionSignal,
    TerminologyProfile,
    TopicSignal,
)
from geo_intelligence.recommendations import build_platform_recommendations
from geo_intelligence.service import (
    DEFAULT_COMPETITORS,
    DEFAULT_SITE_TOPICS,
    build_research_prompt,
    run_geo_intelligence,
)

__all__ = [
    "GEO_DISCLAIMER",
    "METHODOLOGY_NOTE",
    "DEFAULT_COMPETITORS",
    "DEFAULT_ENGINE_CODES",
    "DEFAULT_SITE_TOPICS",
    "ENGINE_META",
    "CitationSignal",
    "EntityMention",
    "GeoExtractionResult",
    "GeoIntelligenceReport",
    "KeywordSignal",
    "PeacockAIGateway",
    "PlatformRecommendation",
    "ProviderResponse",
    "QuestionSignal",
    "TerminologyProfile",
    "TopicSignal",
    "build_platform_recommendations",
    "build_research_prompt",
    "default_simulated_responses",
    "extract_geo_intelligence",
    "run_geo_intelligence",
]
