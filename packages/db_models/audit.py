from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from db_models.base import Base, OrganisationScopedMixin, TimestampMixin


class AuditLog(Base, TimestampMixin, OrganisationScopedMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id"), nullable=False, index=True
    )
    actor_user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    workspace_id: Mapped[str | None] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
