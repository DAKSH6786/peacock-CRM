"""Peacock Agentic Web Readiness API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckSignalRequest(BaseModel):
    check_code: str = Field(min_length=1, max_length=64)
    score: float = Field(ge=0.0, le=100.0)
    evidence_summary: str = ""
    machine_operable_signal: str | None = None


class ReadinessBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    business_type: str = Field(default="mixed", pattern="^(commerce|services|mixed)$")
    signals: list[CheckSignalRequest] = Field(default_factory=list)


class AgenticReadinessRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: ReadinessBriefRequest
    notes: str | None = None


class CheckResultResponse(BaseModel):
    check_code: str
    check_label: str
    score: float
    weight: float
    passed: bool
    evidence_summary: str
    machine_operable_signal: str | None


class GapResponse(BaseModel):
    check_code: str
    title: str
    severity: str
    recommendation: str
    priority: int


class AgenticReadinessResponse(BaseModel):
    analysis_id: str
    name: str
    client_brand: str
    methodology: str
    agent_readiness_score: float
    readiness_band: str
    checks: list[CheckResultResponse]
    gaps: list[GapResponse]
    checks_passed: int
    checks_total: int
    separate_from_seo_aeo_geo: bool
    surface_separation_note: str
    not_industry_standard: bool
    not_industry_standard_note: str
    methodology_note: str
    summary: str


class AgenticReadinessCatalogResponse(BaseModel):
    discoverability_checks: dict[str, str]
    check_codes: list[str]
    methodology: str
    methodology_note: str
    surface_separation_note: str
    not_industry_standard_note: str
    separate_from_seo_aeo_geo: bool
    not_industry_standard: bool
    readiness_bands: list[str]
