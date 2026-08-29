"""Typed specs for Peacock Content Lab."""

from __future__ import annotations

from dataclasses import dataclass, field

from content_lab.scoring import ProposalInput, ProposalScore


@dataclass
class ContentLabSpec:
    website_id: str
    name: str
    client_brand: str
    proposals: list[ProposalInput] = field(default_factory=list)
    topic_cluster: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ContentLabReport:
    analysis_id: str
    client_brand: str
    methodology: str
    citability_is_proprietary_estimate: bool
    citability_disclaimer: str
    proposals: list[ProposalScore]
    example_moat: list[dict]
    top_recommendation: dict | None
