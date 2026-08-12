"""Peacock 90 2.0 — adaptive 90-day roadmap optimisation engine.

Generates a maximum-impact roadmap within resource constraints (budget, writers,
developers, SEO team, content/approval capacity, priorities, risk tolerance).
Never recommends work the organisation cannot execute. Tasks form a dependency
graph (e.g. fix canonical → recrawl → update content → request indexing → monitor).
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


HORIZON_DAYS = 90
METHODOLOGY = "peacock_90_2_adaptive_optimisation"
METHODOLOGY_NOTE = (
    "Peacock 90 2.0 is an adaptive optimisation engine: it maximises roadmap impact "
    "within stated resource constraints and never recommends volume the organisation "
    "cannot execute. Tasks are scheduled with an explicit dependency graph."
)

CAPACITY_GUARDRAIL = (
    "Peacock must not recommend work beyond available budget, headcount, content "
    "capacity, or approval capacity. Infeasible aspirational plans are refused and recorded."
)

RISK_TOLERANCE_LEVELS: tuple[str, ...] = ("low", "medium", "high")

PRIORITY_CODES: tuple[str, ...] = (
    "technical_seo",
    "content",
    "authority",
    "geo_aeo",
    "conversion",
    "brand",
)

TASK_KINDS: tuple[str, ...] = (
    "technical",
    "crawl",
    "content",
    "indexing",
    "monitoring",
    "authority",
    "geo",
    "approval",
    "other",
)


class Peacock90Plan(Base, WorkspaceTenantMixin):
    """One adaptive 90-day roadmap optimisation run."""

    __tablename__ = "peacock90_plans"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    horizon_days: Mapped[int] = mapped_column(Integer, default=HORIZON_DAYS, nullable=False)
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    plan_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    # Resource constraints (inputs)
    budget_amount: Mapped[float] = mapped_column(Float, nullable=False)
    budget_currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    writers: Mapped[int] = mapped_column(Integer, nullable=False)
    developers: Mapped[int] = mapped_column(Integer, nullable=False)
    seo_specialists: Mapped[int] = mapped_column(Integer, nullable=False)
    articles_per_month_max: Mapped[int] = mapped_column(Integer, nullable=False)
    approval_capacity_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_tolerance: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    business_priorities: Mapped[str] = mapped_column(Text, nullable=False)  # comma-separated
    capacity_guardrail: Mapped[str] = mapped_column(Text, nullable=False)
    # Optimisation outputs
    total_impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    budget_used: Mapped[float] = mapped_column(Float, nullable=False)
    articles_planned: Mapped[int] = mapped_column(Integer, nullable=False)
    initiatives_selected: Mapped[int] = mapped_column(Integer, nullable=False)
    initiatives_rejected: Mapped[int] = mapped_column(Integer, nullable=False)
    tasks_scheduled: Mapped[int] = mapped_column(Integer, nullable=False)
    utilisation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    initiatives: Mapped[list[P90Initiative]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", passive_deletes=True
    )
    tasks: Mapped[list[P90Task]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", passive_deletes=True
    )
    dependencies: Mapped[list[P90Dependency]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", passive_deletes=True
    )
    capacity_refusals: Mapped[list[P90CapacityRefusal]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", passive_deletes=True
    )


class P90Initiative(Base, WorkspaceTenantMixin):
    """Candidate workstream — selected or rejected by the optimiser."""

    __tablename__ = "p90_initiatives"
    __table_args__ = (UniqueConstraint("plan_id", "initiative_code"),)

    plan_id: Mapped[str] = mapped_column(
        ForeignKey("peacock90_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    initiative_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority_family: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    effort_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    budget_cost: Mapped[float] = mapped_column(Float, nullable=False)
    writer_days: Mapped[float] = mapped_column(Float, nullable=False)
    developer_days: Mapped[float] = mapped_column(Float, nullable=False)
    seo_days: Mapped[float] = mapped_column(Float, nullable=False)
    articles_required: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    approval_slots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rank: Mapped[int | None] = mapped_column(Integer)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    plan: Mapped[Peacock90Plan] = relationship(back_populates="initiatives")
    tasks: Mapped[list[P90Task]] = relationship(back_populates="initiative")


class P90Task(Base, WorkspaceTenantMixin):
    """Scheduled task node in the dependency graph."""

    __tablename__ = "p90_tasks"
    __table_args__ = (UniqueConstraint("plan_id", "task_code"),)

    plan_id: Mapped[str] = mapped_column(
        ForeignKey("peacock90_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    initiative_id: Mapped[str | None] = mapped_column(
        ForeignKey("p90_initiatives.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    task_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    task_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    owner_role: Mapped[str] = mapped_column(String(32), nullable=False)  # writer|developer|seo
    week_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1..13
    effort_days: Mapped[float] = mapped_column(Float, nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    plan: Mapped[Peacock90Plan] = relationship(back_populates="tasks")
    initiative: Mapped[P90Initiative | None] = relationship(back_populates="tasks")


class P90Dependency(Base, WorkspaceTenantMixin):
    """Directed dependency edge: predecessor must finish before successor."""

    __tablename__ = "p90_dependencies"
    __table_args__ = (UniqueConstraint("plan_id", "predecessor_task_code", "successor_task_code"),)

    plan_id: Mapped[str] = mapped_column(
        ForeignKey("peacock90_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    predecessor_task_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    successor_task_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    edge_label: Mapped[str | None] = mapped_column(String(128))

    plan: Mapped[Peacock90Plan] = relationship(back_populates="dependencies")


class P90CapacityRefusal(Base, WorkspaceTenantMixin):
    """Explicit record that aspirational work was refused due to capacity."""

    __tablename__ = "p90_capacity_refusals"

    plan_id: Mapped[str] = mapped_column(
        ForeignKey("peacock90_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_label: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_amount: Mapped[float] = mapped_column(Float, nullable=False)
    capacity_limit: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    plan: Mapped[Peacock90Plan] = relationship(back_populates="capacity_refusals")
