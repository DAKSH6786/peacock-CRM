"""Peacock GEO Lab — controlled generative-engine experimentation with cautious causality."""

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


# Preset content variants for GEO experiments
VARIANT_PRESETS: dict[str, str] = {
    "A": "original_page",
    "B": "improved_evidence",
    "C": "better_structured_answers",
    "D": "original_dataset_added",
}

VARIANT_CODES: tuple[str, ...] = ("A", "B", "C", "D")

# Metrics tracked before/after
GEO_LAB_METRICS: tuple[str, ...] = (
    "seo",
    "retrieval",
    "ai_mention",
    "ai_citation",
    "answer_prominence",
    "organic_performance",
)

# Page roles in experiment design
PAGE_ROLES: tuple[str, ...] = (
    "control",
    "test",
)

# Strength of causal claim — ordered from weakest to strongest
CAUSALITY_LEVELS: tuple[str, ...] = (
    "correlation",
    "likely_contribution",
    "controlled_experiment",
    "causal_evidence",
)

CAUSALITY_WARNING = (
    "CAUSALITY WARNING: Peacock GEO Lab does NOT automatically conclude that "
    "Change X caused a visibility improvement. Observed lifts may reflect "
    "correlation, seasonality, concurrent changes, engine drift, or noise. "
    "Always distinguish Correlation, Likely contribution, Controlled experiment, "
    "and Causal evidence. Prefer control pages, matched groups, before/after "
    "windows, and time series before upgrading a claim."
)

METHODOLOGY = "peacock_geo_lab_controlled_experimentation"

METHODOLOGY_NOTE = (
    "Peacock GEO Lab is controlled generative-engine experimentation: compare "
    "content variants (e.g. A original, B improved evidence, C structured answers, "
    "D original dataset) with control/test pages, matched groups, before/after "
    "and time-series metrics (SEO, retrieval, AI mention, AI citation, answer "
    "prominence, organic performance). Causality is classified cautiously — "
    "never auto-attributed."
)


class GeoLabExperiment(Base, WorkspaceTenantMixin):
    """A controlled GEO experiment comparing content variants."""

    __tablename__ = "geo_lab_experiments"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic_cluster: Mapped[str | None] = mapped_column(String(255), index=True)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    experiment_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    design_type: Mapped[str] = mapped_column(
        String(64), default="before_after_with_controls", nullable=False, index=True
    )
    # ISO date strings for analysis windows
    pre_window_start: Mapped[str | None] = mapped_column(String(32))
    pre_window_end: Mapped[str | None] = mapped_column(String(32))
    post_window_start: Mapped[str | None] = mapped_column(String(32))
    post_window_end: Mapped[str | None] = mapped_column(String(32))
    intervention_date: Mapped[str | None] = mapped_column(String(32), index=True)
    has_control_pages: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_matched_groups: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_time_series: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    causality_warning: Mapped[str] = mapped_column(Text, nullable=False)
    overall_causality_level: Mapped[str] = mapped_column(
        String(32), default="correlation", nullable=False, index=True
    )
    overall_summary: Mapped[str | None] = mapped_column(Text)
    methodology: Mapped[str] = mapped_column(
        String(64), default=METHODOLOGY, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    variants: Mapped[list[GlVariant]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan", passive_deletes=True
    )
    pages: Mapped[list[GlPage]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan", passive_deletes=True
    )
    observations: Mapped[list[GlMetricObservation]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan", passive_deletes=True
    )
    deltas: Mapped[list[GlMetricDelta]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan", passive_deletes=True
    )
    causality_assessments: Mapped[list[GlCausalityAssessment]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan", passive_deletes=True
    )


class GlVariant(Base, WorkspaceTenantMixin):
    """Content variant under test (A/B/C/D or custom)."""

    __tablename__ = "gl_variants"
    __table_args__ = (UniqueConstraint("experiment_id", "variant_code"),)

    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("geo_lab_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    treatment_description: Mapped[str] = mapped_column(Text, nullable=False)
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)

    experiment: Mapped[GeoLabExperiment] = relationship(back_populates="variants")
    pages: Mapped[list[GlPage]] = relationship(back_populates="variant")


class GlPage(Base, WorkspaceTenantMixin):
    """Control or test page assigned to a variant and optional matched group."""

    __tablename__ = "gl_pages"
    __table_args__ = (UniqueConstraint("experiment_id", "url"),)

    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("geo_lab_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id: Mapped[str | None] = mapped_column(
        ForeignKey("gl_variants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    page_role: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    matched_group: Mapped[str | None] = mapped_column(String(64), index=True)
    match_key: Mapped[str | None] = mapped_column(String(255))  # topic/intent match key

    experiment: Mapped[GeoLabExperiment] = relationship(back_populates="pages")
    variant: Mapped[GlVariant | None] = relationship(back_populates="pages")


class GlMetricObservation(Base, WorkspaceTenantMixin):
    """Time-series observation of a GEO Lab metric for a page."""

    __tablename__ = "gl_metric_observations"
    __table_args__ = (
        UniqueConstraint("experiment_id", "page_id", "metric_code", "observed_at"),
    )

    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("geo_lab_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_id: Mapped[str] = mapped_column(
        ForeignKey("gl_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    observed_at: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    period: Mapped[str] = mapped_column(
        String(16), nullable=False, index=True
    )  # pre|post|during
    value: Mapped[float] = mapped_column(Float, nullable=False)
    engine: Mapped[str | None] = mapped_column(String(64), index=True)
    notes: Mapped[str | None] = mapped_column(Text)

    experiment: Mapped[GeoLabExperiment] = relationship(back_populates="observations")


class GlMetricDelta(Base, WorkspaceTenantMixin):
    """Before/after delta for a metric on a page or variant aggregate."""

    __tablename__ = "gl_metric_deltas"
    __table_args__ = (
        UniqueConstraint("experiment_id", "scope_type", "scope_id", "metric_code"),
    )

    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("geo_lab_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # page|variant|control_pool|test_pool|matched_group
    scope_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    pre_mean: Mapped[float] = mapped_column(Float, nullable=False)
    post_mean: Mapped[float] = mapped_column(Float, nullable=False)
    absolute_delta: Mapped[float] = mapped_column(Float, nullable=False)
    relative_delta_pct: Mapped[float | None] = mapped_column(Float)
    control_adjusted_delta: Mapped[float | None] = mapped_column(Float)
    observation_count_pre: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observation_count_post: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    experiment: Mapped[GeoLabExperiment] = relationship(back_populates="deltas")


class GlCausalityAssessment(Base, WorkspaceTenantMixin):
    """Cautious causality classification for a metric lift — never auto-causal."""

    __tablename__ = "gl_causality_assessments"
    __table_args__ = (UniqueConstraint("experiment_id", "metric_code", "variant_code"),)

    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("geo_lab_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    variant_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    causality_level: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    claim_allowed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Explicit rejection of automatic "X caused Y"
    auto_causal_conclusion_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    confounds_noted: Mapped[str | None] = mapped_column(Text)
    design_supports: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # csv of design features used
    confidence_note: Mapped[str] = mapped_column(Text, nullable=False)

    experiment: Mapped[GeoLabExperiment] = relationship(
        back_populates="causality_assessments"
    )
