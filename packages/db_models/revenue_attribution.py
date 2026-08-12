"""Peacock Revenue Attribution — connect visibility to business value with uncertainty.

Maps Recommendation → Content → Visibility → Traffic → Lead → Conversion → Revenue.
Integrates GA4, CRM, Search Console, conversions, pipeline, transactions, and leads
where available. Attribution includes uncertainty and does not overclaim causality.
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


FUNNEL_STAGES: tuple[str, ...] = (
    "recommendation",
    "content",
    "visibility",
    "traffic",
    "lead",
    "conversion",
    "revenue",
)

STAGE_LABELS: dict[str, str] = {
    "recommendation": "Recommendation",
    "content": "Content",
    "visibility": "Visibility",
    "traffic": "Traffic",
    "lead": "Lead",
    "conversion": "Conversion",
    "revenue": "Revenue",
}

DATA_SOURCES: tuple[str, ...] = (
    "ga4",
    "crm",
    "search_console",
    "conversions",
    "pipeline",
    "transactions",
    "leads",
    "peacock_internal",
)

SOURCE_LABELS: dict[str, str] = {
    "ga4": "GA4",
    "crm": "CRM",
    "search_console": "Search Console",
    "conversions": "Conversions",
    "pipeline": "Pipeline",
    "transactions": "Transactions",
    "leads": "Leads",
    "peacock_internal": "Peacock internal",
}

# Causality posture — never auto-claim revenue causation from visibility alone
CAUSALITY_LEVELS: tuple[str, ...] = (
    "insufficient_data",
    "correlation",
    "likely_contribution",
    "multi_touch_model",
    "causal_evidence",
)

CAUSALITY_WARNING = (
    "CAUSALITY WARNING: Peacock Revenue Attribution does NOT claim that visibility "
    "alone caused revenue. Observed links across Recommendation → Content → "
    "Visibility → Traffic → Lead → Conversion → Revenue may reflect correlation, "
    "seasonality, paid overlap, CRM lag, or missing data. Always report uncertainty "
    "ranges and do not overclaim causality."
)

METHODOLOGY = "peacock_revenue_attribution_uncertain_chain"
METHODOLOGY_NOTE = (
    "Peacock Revenue Attribution attempts to connect visibility to business value "
    "by chaining Recommendation → Content → Visibility → Traffic → Lead → "
    "Conversion → Revenue, integrating GA4, CRM, Search Console, conversions, "
    "pipeline, transactions, and leads where available. Every estimate includes "
    "uncertainty; causality is classified cautiously and never overclaimed."
)


class RevenueAttributionAnalysis(Base, WorkspaceTenantMixin):
    """One revenue attribution chain assessment."""

    __tablename__ = "revenue_attribution_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    causality_warning: Mapped[str] = mapped_column(Text, nullable=False)
    overall_causality_level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    overall_uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    data_completeness: Mapped[float] = mapped_column(Float, nullable=False)
    # Attributed revenue as a range — never a fake point
    attributed_revenue_low: Mapped[float] = mapped_column(Float, nullable=False)
    attributed_revenue_high: Mapped[float] = mapped_column(Float, nullable=False)
    attributed_revenue_mid: Mapped[float | None] = mapped_column(Float)
    sources_available: Mapped[str] = mapped_column(Text, nullable=False)  # comma-separated
    sources_missing: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    stages: Mapped[list[RaFunnelStage]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    links: Mapped[list[RaChainLink]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    source_snapshots: Mapped[list[RaSourceSnapshot]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class RaFunnelStage(Base, WorkspaceTenantMixin):
    """Observed/estimated metric at one funnel stage."""

    __tablename__ = "ra_funnel_stages"
    __table_args__ = (UniqueConstraint("analysis_id", "stage_code"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("revenue_attribution_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stage_label: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    value_low: Mapped[float] = mapped_column(Float, nullable=False)
    value_high: Mapped[float] = mapped_column(Float, nullable=False)
    value_mid: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    data_quality: Mapped[float] = mapped_column(Float, nullable=False)
    primary_source: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[RevenueAttributionAnalysis] = relationship(back_populates="stages")


class RaChainLink(Base, WorkspaceTenantMixin):
    """Edge between consecutive funnel stages with conversion rate range + causality."""

    __tablename__ = "ra_chain_links"
    __table_args__ = (
        UniqueConstraint("analysis_id", "from_stage", "to_stage"),
    )

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("revenue_attribution_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_stage: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    to_stage: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    rate_low: Mapped[float] = mapped_column(Float, nullable=False)
    rate_high: Mapped[float] = mapped_column(Float, nullable=False)
    causality_level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[RevenueAttributionAnalysis] = relationship(back_populates="links")


class RaSourceSnapshot(Base, WorkspaceTenantMixin):
    """Which integrations contributed (or were missing) for this analysis."""

    __tablename__ = "ra_source_snapshots"
    __table_args__ = (UniqueConstraint("analysis_id", "source_code"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("revenue_attribution_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_label: Mapped[str] = mapped_column(String(64), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    contribution_note: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[RevenueAttributionAnalysis] = relationship(
        back_populates="source_snapshots"
    )
