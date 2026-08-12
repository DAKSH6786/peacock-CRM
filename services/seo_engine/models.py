"""Shared result models for Peacock SEO Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from scoring import ScoreResult

Severity = Literal["critical", "warning", "opportunity", "info"]
Priority = Literal["critical", "high", "medium", "low"]


@dataclass(slots=True)
class SeoFinding:
    code: str
    severity: Severity
    title: str
    description: str
    category: str
    page_urls: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SeoRecommendation:
    code: str
    title: str
    priority: Priority
    impact: float  # 0–1
    effort: float  # 0–1
    confidence: float  # 0–1
    affected_pages: list[str]
    reason: str
    suggested_fix: str
    category: str
    priority_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PageIssueSummary:
    url: str
    issues: list[str] = field(default_factory=list)
    severities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SeoAuditReport:
    """Full actionable SEO audit produced from crawl (+ optional connectors)."""

    id: str
    organisation_id: str
    workspace_id: str
    website_id: str | None
    crawl_id: str | None
    status: str
    title: str
    summary: str
    peacock_seo_score: ScoreResult
    scores: dict[str, ScoreResult]
    findings: list[SeoFinding]
    recommendations: list[SeoRecommendation]
    page_issues: list[PageIssueSummary]
    connector_signals: dict[str, Any] = field(default_factory=dict)
    interpretation: str | None = None  # optional LLM narrative — never the numeric score

    @property
    def critical_issues(self) -> list[SeoFinding]:
        return [f for f in self.findings if f.severity == "critical"]

    @property
    def warnings(self) -> list[SeoFinding]:
        return [f for f in self.findings if f.severity == "warning"]

    @property
    def opportunities(self) -> list[SeoFinding]:
        return [f for f in self.findings if f.severity == "opportunity"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "workspace_id": self.workspace_id,
            "website_id": self.website_id,
            "crawl_id": self.crawl_id,
            "status": self.status,
            "title": self.title,
            "summary": self.summary,
            "peacock_seo_score": self.peacock_seo_score.to_dict(),
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "findings": [f.to_dict() for f in self.findings],
            "critical_issues": [f.to_dict() for f in self.critical_issues],
            "warnings": [f.to_dict() for f in self.warnings],
            "opportunities": [f.to_dict() for f in self.opportunities],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "page_issues": [p.to_dict() for p in self.page_issues],
            "connector_signals": self.connector_signals,
            "interpretation": self.interpretation,
        }
