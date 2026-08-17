from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RateLimitPolicySchema(BaseModel):
    max_calls_per_minute: int = Field(default=6, ge=1, le=30)
    max_concurrent: int = Field(default=1, ge=1, le=3)
    max_total_calls: int = Field(default=500, ge=1, le=2000)
    min_interval_ms: int = Field(default=1500, ge=500)
    target_repetitions: int = Field(default=5, ge=1, le=50)
    max_repetitions: int = Field(default=20, ge=1, le=50)


class ProbeCellSchema(BaseModel):
    prompt_text: str = Field(min_length=3, max_length=4000)
    engine_code: str
    model_code: str | None = None
    location_code: str = "global"
    persona_code: str = "default"
    config_code: str = "temp_0.2"
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    time_bucket: str = "current"
    target_repetitions: int | None = Field(default=None, ge=1, le=50)


class VisibilityCampaignRequest(BaseModel):
    website_id: str
    name: str = Field(min_length=1, max_length=255)
    brand_name: str = Field(min_length=1, max_length=255)
    cells: list[ProbeCellSchema] = Field(min_length=1)
    competitors: list[str] = Field(default_factory=list)
    rate_limit: RateLimitPolicySchema = Field(default_factory=RateLimitPolicySchema)
    notes: str | None = None
    workspace_id: str | None = None


class VisibilityCampaignResponse(BaseModel):
    campaign_id: str
    status: str
    brand_name: str
    target_repetitions: int
    rate_limit: dict[str, Any]
    cell_count: int
    single_shot_rejected: bool = True


class VisibilityScoreCardResponse(BaseModel):
    ai_visibility_score: float
    measurement_confidence: str
    peacock_visibility_confidence: float
    based_on: dict[str, int]
    brand_mention_probability: float
    citation_probability: float
    top3_recommendation_probability: float
    competitor_probabilities: dict[str, float] = Field(default_factory=dict)
    distributions: list[dict[str, Any]] = Field(default_factory=list)
    summary: str
    computed_at: str | None = None
    single_shot_rejected: bool = True
    defensible: bool = False
    probe_mode: str = "mock_deterministic"
