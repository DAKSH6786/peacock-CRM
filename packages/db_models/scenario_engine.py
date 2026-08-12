"""Peacock Scenario Engine — counterfactual strategy comparison with projected ranges.

Compares strategies (do nothing, technical SEO, content, authority, SEO/GEO mixes,
Peacock recommended) and returns ranges rather than fake precision, with confidence,
assumptions, data quality, and uncertainty.
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


STRATEGY_CODES: tuple[str, ...] = (
    "do_nothing",
    "fix_technical_seo",
    "publish_more_content",
    "refresh_existing_content",
    "build_topical_authority",
    "build_third_party_authority",
    "seo_only",
    "geo_only",
    "seo_aeo_geo",
    "peacock_recommended",
)

STRATEGY_LABELS: dict[str, str] = {
    "do_nothing": "Do nothing",
    "fix_technical_seo": "Fix technical SEO",
    "publish_more_content": "Publish more content",
    "refresh_existing_content": "Refresh existing content",
    "build_topical_authority": "Build topical authority",
    "build_third_party_authority": "Build third-party authority",
    "seo_only": "SEO-only strategy",
    "geo_only": "GEO-only strategy",
    "seo_aeo_geo": "SEO + AEO + GEO",
    "peacock_recommended": "Peacock recommended strategy",
}

# Default metric for the product example
DEFAULT_METRIC = "organic_visibility_90d"
DEFAULT_METRIC_LABEL = "Projected 90-Day Organic Visibility"

METHODOLOGY = "peacock_scenario_engine_counterfactual_ranges"

METHODOLOGY_NOTE = (
    "Peacock Scenario Engine compares counterfactual strategies and returns projected "
    "ranges rather than fake precision. Every scenario includes confidence, assumptions, "
    "data quality, and uncertainty. Point forecasts are intentionally avoided."
)

RANGES_NOT_FAKE_PRECISION = (
    "Projections are ranges, not single-point precision. Do not present midpoints as "
    "guarantees; use low–high bands with explicit uncertainty."
)


class ScenarioAnalysis(Base, WorkspaceTenantMixin):
    """A counterfactual scenario comparison run."""

    __tablename__ = "scenario_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    primary_metric: Mapped[str] = mapped_column(
        String(64), default=DEFAULT_METRIC, nullable=False, index=True
    )
    primary_metric_label: Mapped[str] = mapped_column(String(255), nullable=False)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default=METHODOLOGY, nullable=False
    )
    ranges_not_fake_precision: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    ranges_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    overall_data_quality: Mapped[float] = mapped_column(Float, nullable=False)
    overall_uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    assumptions_summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_strategy_code: Mapped[str | None] = mapped_column(String(64), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    scenarios: Mapped[list[SeScenario]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    assumptions: Mapped[list[SeAssumption]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class SeScenario(Base, WorkspaceTenantMixin):
    """One counterfactual strategy with projected range outcomes."""

    __tablename__ = "se_scenarios"
    __table_args__ = (UniqueConstraint("analysis_id", "strategy_code"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("scenario_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy_label: Mapped[str] = mapped_column(String(255), nullable=False)
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_peacock_recommended: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # Range projection for primary metric (percent change)
    range_low_pct: Mapped[float] = mapped_column(Float, nullable=False)
    range_high_pct: Mapped[float] = mapped_column(Float, nullable=False)
    # Optional midpoint for display only — not a precision claim
    range_mid_pct: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    data_quality: Mapped[float] = mapped_column(Float, nullable=False)
    uncertainty: Mapped[float] = mapped_column(Float, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    analysis: Mapped[ScenarioAnalysis] = relationship(back_populates="scenarios")
    metric_ranges: Mapped[list[SeMetricRange]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan", passive_deletes=True
    )


class SeMetricRange(Base, WorkspaceTenantMixin):
    """Projected range for an additional metric under a scenario."""

    __tablename__ = "se_metric_ranges"
    __table_args__ = (UniqueConstraint("scenario_id", "metric_code"),)

    scenario_id: Mapped[str] = mapped_column(
        ForeignKey("se_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_label: Mapped[str] = mapped_column(String(255), nullable=False)
    range_low_pct: Mapped[float] = mapped_column(Float, nullable=False)
    range_high_pct: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="percent_change", nullable=False)

    scenario: Mapped[SeScenario] = relationship(back_populates="metric_ranges")


class SeAssumption(Base, WorkspaceTenantMixin):
    """Explicit assumption underpinning the counterfactual comparison."""

    __tablename__ = "se_assumptions"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("scenario_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assumption_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    sensitivity: Mapped[str] = mapped_column(
        String(32), default="medium", nullable=False
    )  # low|medium|high
    affects_strategies: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[ScenarioAnalysis] = relationship(back_populates="assumptions")
