"""Peacock Growth Loop API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GrowthLoopRunRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048, description="Public website URL to run the Growth Loop on.")
    competitor_url: str | None = Field(default=None, max_length=2048)
    max_pages: int = Field(default=6, ge=1, le=20)
    engine_codes: list[str] | None = None
