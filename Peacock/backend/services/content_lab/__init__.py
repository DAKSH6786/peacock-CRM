"""Peacock Content Lab — multi-opportunity content evaluation."""

from db_models.content_lab import (
    CITABILITY_COMPONENTS,
    CITABILITY_DISCLAIMER,
    INFO_GAIN_PENALTIES,
    INFO_GAIN_REWARDS,
    MOAT_FORMAT_PRIORS,
    OPPORTUNITY_DIMENSIONS,
)
from content_lab.models import ContentLabReport, ContentLabSpec
from content_lab.scoring import ProposalInput, evaluate_proposals
from content_lab.service import ContentLabService

__all__ = [
    "CITABILITY_COMPONENTS",
    "CITABILITY_DISCLAIMER",
    "INFO_GAIN_PENALTIES",
    "INFO_GAIN_REWARDS",
    "MOAT_FORMAT_PRIORS",
    "OPPORTUNITY_DIMENSIONS",
    "ContentLabReport",
    "ContentLabService",
    "ContentLabSpec",
    "ProposalInput",
    "evaluate_proposals",
]
