"""Peacock Citation Gap Engine.

Analyses which sources AI platforms actually cited for a brand's category,
fetches those real pages where reachable, and reports the entity/evidence/
source/statistics/authority/content gap versus the client's own crawled site.
"""

from citation_intelligence.gap import analyse_citation_gaps
from citation_intelligence.models import DATA_UNAVAILABLE, CitationGapReport, CitationGapResult

__all__ = ["DATA_UNAVAILABLE", "CitationGapReport", "CitationGapResult", "analyse_citation_gaps"]
