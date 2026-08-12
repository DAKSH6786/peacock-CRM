"""Peacock Action Engine — approval-based autonomous execution layer.

Moves Peacock One beyond recommendations into gated actions. Status lifecycle:
DRAFT → APPROVAL_REQUIRED → APPROVED → EXECUTED | FAILED | REVERTED.

Never make destructive external modifications without explicit permissions.
Future connectors (e.g. CMS) may support changes only when permission is granted.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


ACTION_TYPES: tuple[str, ...] = (
    "create_task",
    "assign_writer",
    "generate_brief",
    "notify_editor",
    "schedule_recrawl",
    "generate_schema_suggestion",
    "prepare_internal_linking_plan",
    "create_outreach_prospect",
    "generate_report",
    "schedule_monitoring",
    # Future connectors (require explicit permission; never auto-run destructive):
    "cms_draft_change",
    "cms_publish",
)

ACTION_LABELS: dict[str, str] = {
    "create_task": "Create task",
    "assign_writer": "Assign writer",
    "generate_brief": "Generate brief",
    "notify_editor": "Notify editor",
    "schedule_recrawl": "Schedule recrawl",
    "generate_schema_suggestion": "Generate schema suggestion",
    "prepare_internal_linking_plan": "Prepare internal linking plan",
    "create_outreach_prospect": "Create outreach prospect",
    "generate_report": "Generate report",
    "schedule_monitoring": "Schedule monitoring",
    "cms_draft_change": "CMS draft change (future connector)",
    "cms_publish": "CMS publish (future connector — destructive)",
}

ACTION_STATUSES: tuple[str, ...] = (
    "DRAFT",
    "APPROVAL_REQUIRED",
    "APPROVED",
    "EXECUTED",
    "FAILED",
    "REVERTED",
)

DESTRUCTIVE_EXTERNAL_ACTIONS: frozenset[str] = frozenset(
    {
        "cms_publish",
        "cms_draft_change",
    }
)

PERMISSION_SCOPES: tuple[str, ...] = (
    "internal_only",
    "notify_external",
    "schedule_external",
    "cms_write",
    "cms_publish",
)

ACTION_PERMISSION_MAP: dict[str, str | None] = {
    "create_task": None,
    "assign_writer": None,
    "generate_brief": None,
    "notify_editor": "notify_external",
    "schedule_recrawl": "schedule_external",
    "generate_schema_suggestion": None,
    "prepare_internal_linking_plan": None,
    "create_outreach_prospect": None,
    "generate_report": None,
    "schedule_monitoring": "schedule_external",
    "cms_draft_change": "cms_write",
    "cms_publish": "cms_publish",
}

DESTRUCTIVE_GUARDRAIL = (
    "Never make destructive external modifications without explicit permissions. "
    "CMS and similar connectors remain DRAFT/APPROVAL_REQUIRED until a matching "
    "connector permission is granted."
)

METHODOLOGY = "peacock_action_engine_approval_based"
METHODOLOGY_NOTE = (
    "Peacock Action Engine is an approval-based execution layer. Actions progress "
    "through DRAFT, APPROVAL_REQUIRED, APPROVED, EXECUTED, FAILED, and REVERTED. "
    "Destructive external modifications are forbidden without explicit permissions."
)


class PeacockAction(Base, WorkspaceTenantMixin):
    """A single gated action request in the Action Engine."""

    __tablename__ = "peacock_actions"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_label: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    payload_summary: Mapped[str] = mapped_column(Text, nullable=False)
    action_status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False, index=True
    )
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_destructive_external: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    permission_scope_required: Mapped[str | None] = mapped_column(String(64), index=True)
    permission_granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), default="low", nullable=False)
    target_ref: Mapped[str | None] = mapped_column(String(255))
    result_summary: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    destructive_guardrail: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    approvals: Mapped[list[PaeApproval]] = relationship(
        back_populates="action", cascade="all, delete-orphan", passive_deletes=True
    )
    executions: Mapped[list[PaeExecution]] = relationship(
        back_populates="action", cascade="all, delete-orphan", passive_deletes=True
    )
    status_events: Mapped[list[PaeStatusEvent]] = relationship(
        back_populates="action", cascade="all, delete-orphan", passive_deletes=True
    )


class PaeConnectorPermission(Base, WorkspaceTenantMixin):
    """Explicit permission grant for external/destructive connectors."""

    __tablename__ = "pae_connector_permissions"
    __table_args__ = (UniqueConstraint("workspace_id", "permission_scope", "connector"),)

    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=True, index=True
    )
    connector: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    permission_scope: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text)


class PaeApproval(Base, WorkspaceTenantMixin):
    """Approval decision on an action."""

    __tablename__ = "pae_approvals"

    action_id: Mapped[str] = mapped_column(
        ForeignKey("peacock_actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(String(32), nullable=False)  # approve|reject
    decided_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(Text)

    action: Mapped[PeacockAction] = relationship(back_populates="approvals")


class PaeExecution(Base, WorkspaceTenantMixin):
    """Execution attempt record (success, failure, or revert)."""

    __tablename__ = "pae_executions"

    action_id: Mapped[str] = mapped_column(
        ForeignKey("peacock_actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    executor: Mapped[str] = mapped_column(String(64), default="internal", nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    external_side_effects: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    action: Mapped[PeacockAction] = relationship(back_populates="executions")


class PaeStatusEvent(Base, WorkspaceTenantMixin):
    """Immutable status transition log."""

    __tablename__ = "pae_status_events"

    action_id: Mapped[str] = mapped_column(
        ForeignKey("peacock_actions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    action: Mapped[PeacockAction] = relationship(back_populates="status_events")
