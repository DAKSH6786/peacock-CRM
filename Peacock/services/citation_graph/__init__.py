"""Peacock Citation Graph — pathways, influence score, source opportunities."""

from db_models.citation_graph import (
    CIS_COMPONENTS,
    FORBIDDEN_TACTICS,
    OPPORTUNITY_TYPES,
    PATHWAY_NODE_KINDS,
    SOURCE_CLASSES,
)
from citation_graph.models import CitationGraphReport, CitationGraphSpec
from citation_graph.opportunity import detect_source_opportunities
from citation_graph.scoring import DEFAULT_CIS_WEIGHTS, aggregate_domain_scores
from citation_graph.service import CitationGraphService

__all__ = [
    "CIS_COMPONENTS",
    "DEFAULT_CIS_WEIGHTS",
    "FORBIDDEN_TACTICS",
    "OPPORTUNITY_TYPES",
    "PATHWAY_NODE_KINDS",
    "SOURCE_CLASSES",
    "CitationGraphReport",
    "CitationGraphService",
    "CitationGraphSpec",
    "aggregate_domain_scores",
    "detect_source_opportunities",
]
