"""Peacock Agentic Web Readiness — Agent Discoverability + Agent Readiness Score.

Analyses whether a business is machine-operable for evolving agent-based search.
Separate from SEO / AEO / GEO. Not a universal industry standard.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


DISCOVERABILITY_CHECKS: tuple[str, ...] = (
    "structured_product_information",
    "clear_pricing",
    "availability",
    "product_ids",
    "schema",
    "api_discoverability",
    "machine_readable_policies",
    "service_descriptions",
    "locations",
    "booking_information",
    "contact_mechanisms",
    "returns",
    "shipping",
    "trust_signals",
)

CHECK_LABELS: dict[str, str] = {
    "structured_product_information": "Structured product information",
    "clear_pricing": "Clear pricing",
    "availability": "Availability",
    "product_ids": "Product IDs",
    "schema": "Schema",
    "api_discoverability": "API discoverability",
    "machine_readable_policies": "Machine-readable policies",
    "service_descriptions": "Service descriptions",
    "locations": "Locations",
    "booking_information": "Booking information",
    "contact_mechanisms": "Contact mechanisms",
    "returns": "Returns",
    "shipping": "Shipping",
    "trust_signals": "Trust signals",
}

# Explicit separation from ranking/visibility surfaces
SURFACE_SEPARATION = (
    "Agent Readiness Score is separate from SEO, AEO, and GEO. "
    "It measures machine-operability / agent discoverability, not classic rankings "
    "or generative citation share."
)

NOT_INDUSTRY_STANDARD = (
    "Peacock Agentic Web Readiness is a proprietary Peacock assessment. "
    "It does not claim universal industry-standard status."
)

METHODOLOGY = "peacock_agentic_web_readiness_v1"
METHODOLOGY_NOTE = (
    "Peacock Agentic Web Readiness evaluates Agent Discoverability across structured "
    "commerce and service signals, then produces an Agent Readiness Score. "
    + SURFACE_SEPARATION
    + " "
    + NOT_INDUSTRY_STANDARD
)

BANDS: tuple[str, ...] = ("nascent", "emerging", "operable", "agent_ready")


class AgenticReadinessAnalysis(Base, WorkspaceTenantMixin):
    """One Agent Discoverability / Agent Readiness assessment."""

    __tablename__ = "agentic_readiness_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(128))
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    # Agent Readiness Score (0–100) — proprietary, not an industry standard
    agent_readiness_score: Mapped[float] = mapped_column(Float, nullable=False)
    readiness_band: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    checks_passed: Mapped[int] = mapped_column(Integer, nullable=False)
    checks_total: Mapped[int] = mapped_column(Integer, nullable=False)
    separate_from_seo_aeo_geo: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    surface_separation_note: Mapped[str] = mapped_column(Text, nullable=False)
    not_industry_standard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    not_industry_standard_note: Mapped[str] = mapped_column(Text, nullable=False)
    methodology_note: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    checks: Mapped[list[AwrCheckResult]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    gaps: Mapped[list[AwrGap]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class AwrCheckResult(Base, WorkspaceTenantMixin):
    """Result for one Agent Discoverability check."""

    __tablename__ = "awr_check_results"
    __table_args__ = (UniqueConstraint("analysis_id", "check_code"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("agentic_readiness_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    check_label: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    machine_operable_signal: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[AgenticReadinessAnalysis] = relationship(back_populates="checks")


class AwrGap(Base, WorkspaceTenantMixin):
    """Prioritised gap that blocks agent machine-operability."""

    __tablename__ = "awr_gaps"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("agentic_readiness_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    check_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)

    analysis: Mapped[AgenticReadinessAnalysis] = relationship(back_populates="gaps")
