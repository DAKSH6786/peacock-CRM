"""Peacock Anomaly Engine — detect and rank visibility/business anomalies.

Detects sudden ranking loss, AI visibility collapse, citation disappearance,
negative sentiment spikes, competitor acceleration, crawler issues, indexation
loss, traffic anomalies, and backlink loss. Ranks anomalies by probable
business impact.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


ANOMALY_TYPES: tuple[str, ...] = (
    "sudden_ranking_loss",
    "ai_visibility_collapse",
    "citation_disappearance",
    "negative_sentiment_spike",
    "competitor_acceleration",
    "crawler_issue",
    "indexation_loss",
    "traffic_anomaly",
    "backlink_loss",
)

ANOMALY_LABELS: dict[str, str] = {
    "sudden_ranking_loss": "Sudden ranking loss",
    "ai_visibility_collapse": "AI visibility collapse",
    "citation_disappearance": "Citation disappearance",
    "negative_sentiment_spike": "Negative sentiment spike",
    "competitor_acceleration": "Competitor acceleration",
    "crawler_issue": "Crawler issue",
    "indexation_loss": "Indexation loss",
    "traffic_anomaly": "Traffic anomaly",
    "backlink_loss": "Backlink loss",
}

# Relative business-impact priors used when ranking (not absolute truth)
IMPACT_PRIORS: dict[str, float] = {
    "sudden_ranking_loss": 0.95,
    "traffic_anomaly": 0.90,
    "ai_visibility_collapse": 0.88,
    "citation_disappearance": 0.85,
    "indexation_loss": 0.82,
    "backlink_loss": 0.75,
    "competitor_acceleration": 0.72,
    "crawler_issue": 0.68,
    "negative_sentiment_spike": 0.65,
}

SEVERITY_LEVELS: tuple[str, ...] = ("low", "medium", "high", "critical")

METHODOLOGY = "peacock_anomaly_engine_impact_ranked"
METHODOLOGY_NOTE = (
    "Peacock Anomaly Engine detects unusual shifts across ranking, AI visibility, "
    "citations, sentiment, competitors, crawlers, indexation, traffic, and backlinks. "
    "Anomalies are ranked by probable business impact using severity, magnitude, "
    "impact priors, and optional revenue exposure — not as guaranteed P&L forecasts."
)


class AnomalyScan(Base, WorkspaceTenantMixin):
    """One anomaly detection scan over a time window."""

    __tablename__ = "anomaly_scans"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scan_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    anomalies_detected: Mapped[int] = mapped_column(Integer, nullable=False)
    critical_count: Mapped[int] = mapped_column(Integer, nullable=False)
    high_count: Mapped[int] = mapped_column(Integer, nullable=False)
    top_anomaly_type: Mapped[str | None] = mapped_column(String(64), index=True)
    top_impact_score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    anomalies: Mapped[list[AeAnomaly]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )


class AeAnomaly(Base, WorkspaceTenantMixin):
    """A single detected anomaly with probable business impact ranking."""

    __tablename__ = "ae_anomalies"
    __table_args__ = (UniqueConstraint("scan_id", "anomaly_type", "detected_at", "title"),)

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("anomaly_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    anomaly_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    anomaly_label: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    magnitude: Mapped[float] = mapped_column(Float, nullable=False)
    z_score: Mapped[float] = mapped_column(Float, nullable=False)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    impact_rank: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    revenue_exposure: Mapped[float | None] = mapped_column(Float)
    metric_key: Mapped[str | None] = mapped_column(String(128), index=True)
    baseline_value: Mapped[float | None] = mapped_column(Float)
    current_value: Mapped[float | None] = mapped_column(Float)
    recommended_response: Mapped[str] = mapped_column(Text, nullable=False)
    is_noise: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    scan: Mapped[AnomalyScan] = relationship(back_populates="anomalies")
