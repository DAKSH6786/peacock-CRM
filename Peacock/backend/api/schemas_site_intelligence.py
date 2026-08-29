"""Peacock Site Intelligence API schemas (enterprise SEO + GEO report)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SiteIntelligenceAnalyzeRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048, description="Public website URL to crawl and analyse.")
    competitor_url: str | None = Field(
        default=None,
        max_length=2048,
        description="Optional competitor URL to crawl for a real content/entity/topical diff.",
    )
    max_pages: int = Field(default=8, ge=1, le=25, description="Maximum number of pages to crawl (kept small for a responsive report).")
    engine_codes: list[str] | None = Field(
        default=None,
        description="Which AI plugins to broadcast the research prompt to (default: chatgpt, gemini, claude, perplexity, deepseek).",
    )
