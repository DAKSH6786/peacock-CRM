"""Citation Gap Engine — result models.

Every field is either a real measurement (from an actual page fetch or the
client's own crawled content) or an explicit "Data unavailable" string —
never an invented gap.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DATA_UNAVAILABLE = "Data unavailable"


@dataclass(slots=True)
class CitationGapResult:
    cited_url: str
    cited_domain: str
    source_class: str
    engine_codes: list[str]  # which AI plugin(s) cited this URL
    topic_context: str  # the query/topic that produced this citation
    fetch_status: str  # "fetched" | "fetch_failed" | "not_attempted"
    cited_page_title: str | None
    cited_page_word_count: int | None
    entity_gap: list[str]
    evidence_gap: str
    source_gap: bool
    statistics_gap: str
    authority_gap: str
    content_gap: list[str]
    recommended_fix: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CitationGapReport:
    client_brand: str
    citations_observed: int
    citations_analysed: int
    gaps: list[CitationGapResult] = field(default_factory=list)
    disclaimer: str = (
        "Citation gaps are derived from URLs actually cited in collected AI plugin responses "
        "and a real fetch of those pages where reachable — never invented."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "citations_observed": self.citations_observed,
            "citations_analysed": self.citations_analysed,
            "gaps": [g.to_dict() for g in self.gaps],
            "disclaimer": self.disclaimer,
        }
