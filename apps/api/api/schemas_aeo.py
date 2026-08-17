"""AEO API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AeoAnalysisRequest(BaseModel):
    website_id: str
    crawl_id: str
    name: str = Field(min_length=2, max_length=255)
    workspace_id: str | None = None
    page_urls: list[str] = Field(default_factory=list)
    notes: str | None = None


class AeoAnalysisResponse(BaseModel):
    analysis_id: str
    name: str
    website_id: str
    crawl_id: str
    page_count: int
    aeo_score: float
    answerability_score: float
    faq_coverage_score: float
    citation_readiness_score: float
    entity_coverage: float
    question_coverage: float
    pages: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    methodology: str = "aeo_deterministic_answer_readiness"
    scoring_note: str = (
        "Proprietary deterministic estimate from crawled page structure — "
        "not a live answer-engine ranking."
    )
