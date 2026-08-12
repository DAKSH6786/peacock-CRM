"""Typed specs for Share of Answer."""

from __future__ import annotations

from dataclasses import dataclass, field

from share_of_answer.scoring import BrandAggregate, DEFAULT_INDICATOR_WEIGHTS


@dataclass(frozen=True)
class AnswerObservationSpec:
    prompt_text: str
    engine_code: str
    raw_excerpt: str
    model_code: str | None = None
    answer_token_count: int | None = None


@dataclass
class ShareOfAnswerSpec:
    website_id: str
    name: str
    query_cluster: str
    client_brand: str
    competitor_brands: list[str] = field(default_factory=list)
    observations: list[AnswerObservationSpec] = field(default_factory=list)
    notes: str | None = None
    # Optional weight overrides (must still be multi-indicator)
    indicator_weights: dict[str, float] | None = None


@dataclass(frozen=True)
class ShareOfAnswerReport:
    analysis_id: str
    query_cluster: str
    client_brand: str
    methodology: str
    token_count_alone_rejected: bool
    observation_count: int
    brands: list[BrandAggregate]
    indicator_weights: dict[str, float]

    def client_share(self) -> float | None:
        for b in self.brands:
            if b.is_client or b.entity_name.lower() == self.client_brand.lower():
                return b.share_of_answer
        return None
