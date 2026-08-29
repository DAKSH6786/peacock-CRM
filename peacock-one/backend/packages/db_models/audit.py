from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, OrganisationScopedMixin, TimestampMixin


class AuditLog(Base, TimestampMixin, OrganisationScopedMixin):
    """Immutable-ish audit trail. Attribute bags are relational, not JSONB."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), index=True)

    organisation = relationship("Organisation")
    actor = relationship("User")
    workspace = relationship("Workspace")
    attributes: Mapped[list[AuditLogAttribute]] = relationship(
        back_populates="audit_log",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class AuditLogAttribute(Base, TimestampMixin):
    """EAV attributes for audit context (replaces free-form JSONB metadata)."""

    __tablename__ = "audit_log_attributes"
    __table_args__ = (UniqueConstraint("audit_log_id", "key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    audit_log_id: Mapped[str] = mapped_column(
        ForeignKey("audit_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(2000), nullable=False)

    audit_log: Mapped[AuditLog] = relationship(back_populates="attributes")
