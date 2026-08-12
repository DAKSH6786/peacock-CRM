from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db_models.base import Base, OrganisationScopedMixin, TimestampMixin


class BackgroundJob(Base, TimestampMixin, OrganisationScopedMixin):
    """Status tracking for every long-running operation."""

    __tablename__ = "background_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id"), nullable=False, index=True
    )
    workspace_id: Mapped[str | None] = mapped_column(String(36), index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    backend: Mapped[str] = mapped_column(String(32), nullable=False, default="celery")
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)
