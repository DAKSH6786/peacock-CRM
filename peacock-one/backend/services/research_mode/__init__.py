"""Peacock Research Mode — search intelligence laboratory experiments."""

from db_models.research_mode import (
    CAUSALITY_WARNING,
    FINDING_VERDICTS,
    LABORATORY_POSITIONING,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    OBSERVATION_ARMS,
    PAGE_ROLES,
    RESEARCH_METRIC_LABELS,
    RESEARCH_METRICS,
    STUDY_PHASES,
    UNCERTAINTY_BANDS,
)
from research_mode.analysis import (
    ObservationSpec,
    PageSpec,
    PromptSpec,
    ResearchStudySpec,
    analyse_research_study,
    catalog,
)
from research_mode.models import ResearchModeCreateSpec, ResearchModeReport
from research_mode.service import ResearchModeService

__all__ = [
    "CAUSALITY_WARNING",
    "FINDING_VERDICTS",
    "LABORATORY_POSITIONING",
    "METHODOLOGY",
    "METHODOLOGY_NOTE",
    "OBSERVATION_ARMS",
    "PAGE_ROLES",
    "RESEARCH_METRIC_LABELS",
    "RESEARCH_METRICS",
    "STUDY_PHASES",
    "UNCERTAINTY_BANDS",
    "ObservationSpec",
    "PageSpec",
    "PromptSpec",
    "ResearchModeCreateSpec",
    "ResearchModeReport",
    "ResearchModeService",
    "ResearchStudySpec",
    "analyse_research_study",
    "catalog",
]
