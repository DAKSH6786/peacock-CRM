"""Answer entity extraction for Share of Answer.

Produces multi-indicator readings. Mock extractor supports deterministic
tests without claiming token span alone equals influence.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from share_of_answer.scoring import EntityIndicatorReading


@dataclass(frozen=True)
class AnswerDocument:
    prompt_text: str
    engine_code: str
    raw_excerpt: str
    model_code: str | None = None
    answer_token_count: int | None = None


def _seed(text: str, entity: str) -> int:
    return int(hashlib.sha256(f"{text}|{entity}".encode()).hexdigest()[:8], 16)


def _approx_token_count(text: str) -> int:
    return max(1, len(re.findall(r"\S+", text)))


def extract_entity_indicators(
    document: AnswerDocument,
    *,
    client_brand: str,
    competitor_brands: list[str],
) -> list[EntityIndicatorReading]:
    """Extract multi-indicator readings for client + competitors from an answer.

    Uses a deterministic mock when structured signals are not available.
    Real pipelines can replace this with NLP/LLM extraction while keeping
    the same indicator schema.
    """
    entities = [client_brand, *competitor_brands]
    # Deduplicate preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for name in entities:
        key = name.strip()
        if not key or key.lower() in seen:
            continue
        seen.add(key.lower())
        ordered.append(key)

    total_tokens = document.answer_token_count or _approx_token_count(document.raw_excerpt)
    text_l = document.raw_excerpt.lower()

    readings: list[EntityIndicatorReading] = []
    # Rank entities by a mix of explicit mention + seeded prominence
    ranked: list[tuple[str, float]] = []
    for name in ordered:
        s = _seed(document.raw_excerpt + document.prompt_text + document.engine_code, name)
        explicit = name.lower() in text_l
        base = (0.55 if explicit else 0.25) + (s % 100) / 250.0
        ranked.append((name, base))
    ranked.sort(key=lambda x: x[1], reverse=True)

    for rank_idx, (name, _base) in enumerate(ranked):
        s = _seed(document.raw_excerpt + document.engine_code, name)
        explicit = name.lower() in text_l
        mentioned = explicit or (s % 10) < 7
        position = (rank_idx + 1) if mentioned else None

        # Token span is diagnostic — allocate some share but scorer won't use it alone
        span = 0.0
        if mentioned:
            span = 0.08 + (s % 40) / 100.0  # 0.08–0.47
        # Normalise spans later across mentioned entities
        recommendation = 0.0
        if mentioned:
            recommendation = max(0.15, 1.0 - 0.12 * rank_idx) * (0.7 + (s % 30) / 100.0)
            recommendation = min(1.0, recommendation)

        answer_space = 0.0
        if mentioned:
            # Structural slot share declines with rank — independent of exact tokens
            answer_space = max(0.05, 0.45 - 0.08 * rank_idx)

        citation = 0.0
        if mentioned and (s % 10) < 5:
            citation = 0.4 + (s % 50) / 100.0

        semantic = 0.0
        if mentioned:
            semantic = 0.3 + (s % 60) / 100.0
            if position == 1:
                semantic = min(1.0, semantic + 0.15)

        pos_c = neg_c = neu_c = 0
        if mentioned:
            pos_c = 1 + (s % 4)
            neg_c = (s % 3)
            neu_c = (s // 7) % 3

        if not mentioned:
            outcome = "absent"
        elif rank_idx == 0:
            outcome = "win"
        elif rank_idx == 1 and len(ranked) > 2:
            outcome = "tie" if (s % 2) == 0 else "mixed"
        else:
            outcome = "lose" if (s % 5) < 3 else "mixed"

        readings.append(
            EntityIndicatorReading(
                entity_name=name,
                is_client=name.lower() == client_brand.lower(),
                mention=mentioned,
                mention_count=(1 + s % 3) if mentioned else 0,
                position=position,
                recommendation_strength=min(1.0, recommendation),
                answer_space=min(1.0, answer_space),
                citation_ownership=min(1.0, citation),
                semantic_prominence=min(1.0, semantic),
                positive_claims=pos_c,
                negative_claims=neg_c,
                neutral_claims=neu_c,
                comparison_outcome=outcome,
                token_span_ratio=min(1.0, span),
            )
        )

    # Renormalise token spans among mentioned entities for diagnostic fairness
    mentioned_readings = [r for r in readings if r.mention]
    span_sum = sum(r.token_span_ratio for r in mentioned_readings) or 1.0
    normalised: list[EntityIndicatorReading] = []
    for r in readings:
        if r.mention and span_sum > 0:
            normalised.append(
                EntityIndicatorReading(
                    entity_name=r.entity_name,
                    is_client=r.is_client,
                    mention=r.mention,
                    mention_count=r.mention_count,
                    position=r.position,
                    recommendation_strength=r.recommendation_strength,
                    answer_space=r.answer_space,
                    citation_ownership=r.citation_ownership,
                    semantic_prominence=r.semantic_prominence,
                    positive_claims=r.positive_claims,
                    negative_claims=r.negative_claims,
                    neutral_claims=r.neutral_claims,
                    comparison_outcome=r.comparison_outcome,
                    token_span_ratio=r.token_span_ratio / span_sum,
                )
            )
        else:
            normalised.append(r)

    _ = total_tokens  # available for future extractors
    return normalised
