from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SeoAuditRequest(BaseModel):
    crawl_id: str
    fetch_connectors: bool = True
    persist: bool = True


class ScoreResultResponse(BaseModel):
    code: str
    label: str
    score: float
    confidence: float
    inputs_used: list[str] = Field(default_factory=list)
    major_positive_factors: list[str] = Field(default_factory=list)
    major_negative_factors: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class SeoFindingResponse(BaseModel):
    code: str
    severity: str
    title: str
    description: str
    category: str
    page_urls: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class SeoRecommendationResponse(BaseModel):
    code: str
    title: str
    priority: str
    impact: float
    effort: float
    confidence: float
    affected_pages: list[str] = Field(default_factory=list)
    reason: str
    suggested_fix: str
    category: str
    priority_score: float = 0.0


class PageIssueResponse(BaseModel):
    url: str
    issues: list[str] = Field(default_factory=list)
    severities: list[str] = Field(default_factory=list)


class SeoAuditResponse(BaseModel):
    id: str
    organisation_id: str
    workspace_id: str
    website_id: str | None = None
    crawl_id: str | None = None
    status: str
    title: str
    summary: str
    peacock_seo_score: ScoreResultResponse
    scores: dict[str, ScoreResultResponse]
    findings: list[SeoFindingResponse] = Field(default_factory=list)
    critical_issues: list[SeoFindingResponse] = Field(default_factory=list)
    warnings: list[SeoFindingResponse] = Field(default_factory=list)
    opportunities: list[SeoFindingResponse] = Field(default_factory=list)
    recommendations: list[SeoRecommendationResponse] = Field(default_factory=list)
    page_issues: list[PageIssueResponse] = Field(default_factory=list)
    connector_signals: dict[str, Any] = Field(default_factory=dict)
    interpretation: str | None = None
