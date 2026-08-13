"""Peacock Research Mode API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PageRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    page_role: str = Field(default="treatment", max_length=32)
    label: str | None = Field(default=None, max_length=255)


class PromptRequest(BaseModel):
    prompt_text: str = Field(min_length=1)
    prompt_cluster: str | None = Field(default=None, max_length=128)


class ObservationRequest(BaseModel):
    arm: str = Field(min_length=1, max_length=32)
    round_index: int = Field(ge=0)
    page_url: str = Field(min_length=1, max_length=2048)
    page_role: str = Field(min_length=1, max_length=32)
    prompt_text: str = Field(min_length=1)
    value: float
    observed_at: datetime | None = None


class ResearchStudyBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    research_question: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    metric_key: str = Field(min_length=1, max_length=64)
    treatment_description: str = Field(min_length=1)
    pages: list[PageRequest] = Field(default_factory=list)
    prompts: list[PromptRequest] = Field(default_factory=list)
    observations: list[ObservationRequest] = Field(default_factory=list)
    observation_rounds: int = Field(default=3, ge=1, le=30)
    analysed_at: datetime | None = None


class ResearchStudyCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: ResearchStudyBriefRequest
    notes: str | None = None


class PageResponse(BaseModel):
    url: str
    page_role: str
    label: str | None
    rank_order: int


class PromptResponse(BaseModel):
    prompt_text: str
    prompt_cluster: str | None
    rank_order: int


class ObservationResponse(BaseModel):
    arm: str
    round_index: int
    page_url: str
    page_role: str
    prompt_text: str
    metric_key: str
    value: float
    observed_at: str


class FindingResponse(BaseModel):
    finding_index: int
    verdict: str
    claim: str
    evidence: str
    uncertainty_band: str
    uncertainty_rationale: str
    auto_causal_conclusion_rejected: bool
    next_step: str


class ResearchStudyResponse(BaseModel):
    study_id: str
    name: str
    client_brand: str
    methodology: str
    research_question: str
    hypothesis: str
    metric_key: str
    metric_label: str
    treatment_description: str
    completed_phases: list[str]
    pages: list[PageResponse]
    prompts: list[PromptResponse]
    observations: list[ObservationResponse]
    findings: list[FindingResponse]
    baseline_mean: float | None
    treatment_mean: float | None
    absolute_delta: float | None
    relative_delta_pct: float | None
    control_adjusted_delta: float | None
    uncertainty_band: str
    uncertainty_score: float
    finding_verdict: str
    finding_summary: str
    observation_rounds: int
    pages_count: int
    prompts_count: int
    laboratory_positioning: str
    causality_warning: str
    methodology_note: str
    analysed_at: str


class ResearchModeCatalogResponse(BaseModel):
    study_phases: list[str]
    observation_arms: list[str]
    page_roles: list[str]
    research_metrics: list[str]
    research_metric_labels: dict[str, str]
    finding_verdicts: list[str]
    uncertainty_bands: list[str]
    laboratory_positioning: str
    causality_warning: str
    methodology_note: str
    example_research_question: str
    product_note: str


class ResearchModePreviewResponse(BaseModel):
    client_brand: str
    research_question: str
    hypothesis: str
    metric_key: str
    metric_label: str
    treatment_description: str
    completed_phases: list[str]
    pages: list[PageResponse]
    prompts: list[PromptResponse]
    observations: list[ObservationResponse]
    findings: list[FindingResponse]
    baseline_mean: float | None
    treatment_mean: float | None
    absolute_delta: float | None
    relative_delta_pct: float | None
    control_adjusted_delta: float | None
    uncertainty_band: str
    uncertainty_score: float
    finding_verdict: str
    finding_summary: str
    observation_rounds: int
    pages_count: int
    prompts_count: int
    laboratory_positioning: str
    causality_warning: str
    methodology_note: str
    analysed_at: str
