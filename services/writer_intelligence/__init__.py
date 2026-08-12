"""Writer Intelligence 2.0 — proprietary writer decision system."""

from db_models.writer_intelligence import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    OUTCOME_EDGE_TYPES,
    OUTCOME_NODE_KINDS,
    PERFORMANCE_METRICS,
    SIMILARITY_ONLY_REJECTED,
    WRITER_DNA_TRAITS,
)
from writer_intelligence.models import WriterIntelligenceReport, WriterIntelligenceSpec
from writer_intelligence.scoring import (
    ArticleOutcomeHistory,
    DecisionContext,
    WriterCandidate,
    recommend_writers,
)
from writer_intelligence.service import WriterIntelligenceService

__all__ = [
    "METHODOLOGY",
    "METHODOLOGY_NOTE",
    "OUTCOME_EDGE_TYPES",
    "OUTCOME_NODE_KINDS",
    "PERFORMANCE_METRICS",
    "SIMILARITY_ONLY_REJECTED",
    "WRITER_DNA_TRAITS",
    "ArticleOutcomeHistory",
    "DecisionContext",
    "WriterCandidate",
    "WriterIntelligenceReport",
    "WriterIntelligenceService",
    "WriterIntelligenceSpec",
    "recommend_writers",
]
