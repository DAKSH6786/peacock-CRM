"""Typed specs for Retrieval Pathway Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field

from retrieval_pathway.forensics import (
    BottleneckResult,
    CauseResult,
    ForensicReport,
    ObservedEvidenceInput,
)


@dataclass
class RetrievalPathwaySpec:
    website_id: str
    name: str
    query_cluster: str
    client_brand: str
    target_url: str
    evidence: ObservedEvidenceInput
    notes: str | None = None
    competitor_urls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RetrievalPathwayReport:
    analysis_id: str
    query_cluster: str
    client_brand: str
    target_url: str
    target_domain: str
    methodology: str
    proprietary_ranking_access_claimed: bool
    disclaimer: str
    forensic: ForensicReport
    example_display: dict

    @property
    def bottleneck(self) -> BottleneckResult:
        return self.forensic.bottleneck

    @property
    def causes(self) -> list[CauseResult]:
        return self.forensic.causes
