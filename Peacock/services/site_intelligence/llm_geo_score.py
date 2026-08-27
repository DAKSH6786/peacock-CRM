"""Individual ChatGPT / Gemini / Claude / Perplexity / DeepSeek GEO Scores.

Peacock never invents an LLM-visibility number: when a plugin has no live API
key, its GEO Score is reported as unavailable rather than computed from
simulated placeholder text. When a plugin IS live, the score is a
deterministic read of what that specific model's response actually contains
— never a claim that any keyword guarantees ranking or citation.
"""

from __future__ import annotations

from geo_intelligence.extraction import extract_questions
from geo_intelligence.models import GeoExtractionResult, ProviderResponse

from site_intelligence.models import CONFIDENCE_EXPERIMENTAL, PerLlmGeoScore


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, value))


def score_llm_geo(
    response: ProviderResponse,
    *,
    brand: str,
    extraction: GeoExtractionResult,
) -> PerLlmGeoScore:
    entities_here = sorted(
        {e.name for e in extraction.entities if response.engine_code in e.engine_codes}
    )
    questions_here = extract_questions(response.content or "")
    citations_here = sorted(
        {c.domain for c in extraction.citations if c.engine_code == response.engine_code}
    )

    brand_mentioned = bool(brand) and brand.strip().lower() in (response.content or "").lower()

    if response.simulated:
        return PerLlmGeoScore(
            engine_code=response.engine_code,
            engine_name=response.engine_name,
            available=False,
            score=None,
            reason_unavailable=(
                f"{response.engine_name} plugin has no live API key configured — GEO Score is not "
                "computed from simulated placeholder text. Set the corresponding environment variable "
                "to enable a real measurement."
            ),
            brand_mentioned=brand_mentioned,
            entities_mentioned=entities_here[:10],
            questions_raised=questions_here[:5],
            citations=citations_here[:5],
            opportunities=[],
            confidence=CONFIDENCE_EXPERIMENTAL,
        )

    citation_score = _clamp100(len(citations_here) * 20.0)
    entity_score = _clamp100(len(entities_here) * 10.0)
    question_score = _clamp100(len(questions_here) * 15.0)
    brand_score = 100.0 if brand_mentioned else 0.0

    score = round(0.35 * brand_score + 0.25 * citation_score + 0.2 * entity_score + 0.2 * question_score, 2)

    return PerLlmGeoScore(
        engine_code=response.engine_code,
        engine_name=response.engine_name,
        available=True,
        score=score,
        reason_unavailable=None,
        brand_mentioned=brand_mentioned,
        entities_mentioned=entities_here[:10],
        questions_raised=questions_here[:5],
        citations=citations_here[:5],
        opportunities=[],
        confidence="medium",
    )
