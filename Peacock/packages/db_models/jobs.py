from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, OrganisationScopedMixin, TimestampMixin


class BackgroundJob(Base, TimestampMixin, OrganisationScopedMixin):
    """Status tracking for long-running operations.

    ``payload`` / ``result`` remain JSONB because each job name defines a
    different contract (crawl config, probe batch, strategy pack, …).
    Do not use JSONB for fixed identity/tenancy fields — those are columns + FKs.
    """

    __tablename__ = "background_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    backend: Mapped[str] = mapped_column(String(32), nullable=False, default="celery")
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True)

    organisation = relationship("Organisation")
    workspace = relationship("Workspace")
    created_by = relationship("User")
