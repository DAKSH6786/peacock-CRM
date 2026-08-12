"""Peacock Action Engine workflow — approval gates + safe execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.action_engine import (
    ACTION_LABELS,
    ACTION_PERMISSION_MAP,
    ACTION_STATUSES,
    ACTION_TYPES,
    DESTRUCTIVE_EXTERNAL_ACTIONS,
    DESTRUCTIVE_GUARDRAIL,
    METHODOLOGY_NOTE,
    PERMISSION_SCOPES,
)


ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "DRAFT": frozenset({"APPROVAL_REQUIRED", "APPROVED"}),  # APPROVED only if !requires_approval
    "APPROVAL_REQUIRED": frozenset({"APPROVED", "DRAFT", "FAILED"}),
    "APPROVED": frozenset({"EXECUTED", "FAILED", "DRAFT"}),
    "EXECUTED": frozenset({"REVERTED", "FAILED"}),
    "FAILED": frozenset({"DRAFT", "APPROVAL_REQUIRED", "APPROVED"}),
    "REVERTED": frozenset({"DRAFT"}),
}


@dataclass
class ActionDraft:
    action_type: str
    title: str
    payload_summary: str
    description: str | None = None
    target_ref: str | None = None
    risk_level: str = "low"
    requires_approval: bool = True
    notes: str | None = None

    def validate(self) -> None:
        if self.action_type not in ACTION_TYPES:
            raise ValueError(f"Unsupported action_type: {self.action_type}")
        if not self.title.strip():
            raise ValueError("title is required")
        if not self.payload_summary.strip():
            raise ValueError("payload_summary is required")
        if self.risk_level not in ("low", "medium", "high"):
            raise ValueError("risk_level must be low|medium|high")


@dataclass
class ActionSpec:
    website_id: str
    draft: ActionDraft
    granted_permissions: list[str] = field(default_factory=list)
    # scopes already granted for this workspace (e.g. cms_publish)


@dataclass(slots=True)
class TransitionResult:
    from_status: str | None
    to_status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExecutionResult:
    outcome: str  # EXECUTED|FAILED|REVERTED
    detail: str
    external_side_effects: bool
    executor: str = "internal"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ActionView:
    action_type: str
    action_label: str
    title: str
    description: str | None
    payload_summary: str
    action_status: str
    requires_approval: bool
    is_destructive_external: bool
    permission_scope_required: str | None
    permission_granted: bool
    risk_level: str
    target_ref: str | None
    result_summary: str | None
    failure_reason: str | None
    destructive_guardrail: str
    transitions: list[TransitionResult]
    executions: list[ExecutionResult]
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "action_label": self.action_label,
            "title": self.title,
            "description": self.description,
            "payload_summary": self.payload_summary,
            "action_status": self.action_status,
            "requires_approval": self.requires_approval,
            "is_destructive_external": self.is_destructive_external,
            "permission_scope_required": self.permission_scope_required,
            "permission_granted": self.permission_granted,
            "risk_level": self.risk_level,
            "target_ref": self.target_ref,
            "result_summary": self.result_summary,
            "failure_reason": self.failure_reason,
            "destructive_guardrail": self.destructive_guardrail,
            "transitions": [t.to_dict() for t in self.transitions],
            "executions": [e.to_dict() for e in self.executions],
            "notes": self.notes,
        }


def is_destructive_external(action_type: str) -> bool:
    return action_type in DESTRUCTIVE_EXTERNAL_ACTIONS


def required_permission(action_type: str) -> str | None:
    return ACTION_PERMISSION_MAP.get(action_type)


def permission_satisfied(action_type: str, granted: list[str]) -> bool:
    scope = required_permission(action_type)
    if scope is None:
        return True
    return scope in granted


def _simulate_internal_execution(draft: ActionDraft) -> ExecutionResult:
    """Safe internal handlers — no destructive external side effects."""
    handlers = {
        "create_task": "Created internal task record (no external write).",
        "assign_writer": "Writer assignment recorded for approval/handoff.",
        "generate_brief": "Content brief draft generated internally.",
        "notify_editor": "Editor notification queued (connector may deliver).",
        "schedule_recrawl": "Recrawl schedule recorded (connector may enqueue).",
        "generate_schema_suggestion": "Schema suggestion artifact generated (not published).",
        "prepare_internal_linking_plan": "Internal linking plan prepared as draft.",
        "create_outreach_prospect": "Outreach prospect created in draft CRM list.",
        "generate_report": "Report artifact generated internally.",
        "schedule_monitoring": "Monitoring schedule recorded.",
    }
    if draft.action_type in DESTRUCTIVE_EXTERNAL_ACTIONS:
        return ExecutionResult(
            outcome="FAILED",
            detail=(
                f"Blocked: {draft.action_type} is a destructive external action. "
                + DESTRUCTIVE_GUARDRAIL
            ),
            external_side_effects=False,
            executor="guardrail",
        )
    detail = handlers.get(
        draft.action_type, f"Executed internal action {draft.action_type}."
    )
    # notify/schedule may eventually hit connectors but current executor is internal stub
    external = draft.action_type in (
        "notify_editor",
        "schedule_recrawl",
        "schedule_monitoring",
    )
    return ExecutionResult(
        outcome="EXECUTED",
        detail=detail + f" Payload: {draft.payload_summary}",
        external_side_effects=external,
        executor="internal",
    )


def create_action_view(
    draft: ActionDraft,
    *,
    granted_permissions: list[str] | None = None,
) -> ActionView:
    """Create a new action in DRAFT (or APPROVAL_REQUIRED if approval needed)."""
    draft.validate()
    granted = list(granted_permissions or [])
    destructive = is_destructive_external(draft.action_type)
    scope = required_permission(draft.action_type)
    permitted = permission_satisfied(draft.action_type, granted)

    # Destructive external always starts needing approval + permission
    requires_approval = draft.requires_approval or destructive
    if destructive and not permitted:
        # Stay in DRAFT until permission exists; still surface guardrail
        status = "DRAFT"
        reason = (
            "Created as DRAFT. Destructive external action awaits explicit connector "
            f"permission ({scope}) before approval/execution."
        )
    elif requires_approval:
        status = "APPROVAL_REQUIRED"
        reason = "Created and submitted for approval."
    else:
        status = "APPROVED"
        reason = "Created as auto-approved (requires_approval=false)."

    transitions = [TransitionResult(from_status=None, to_status=status, reason=reason)]
    return ActionView(
        action_type=draft.action_type,
        action_label=ACTION_LABELS[draft.action_type],
        title=draft.title.strip(),
        description=draft.description,
        payload_summary=draft.payload_summary.strip(),
        action_status=status,
        requires_approval=requires_approval,
        is_destructive_external=destructive,
        permission_scope_required=scope,
        permission_granted=permitted,
        risk_level=draft.risk_level,
        target_ref=draft.target_ref,
        result_summary=None,
        failure_reason=None,
        destructive_guardrail=DESTRUCTIVE_GUARDRAIL,
        transitions=transitions,
        executions=[],
        notes=draft.notes,
    )


def submit_for_approval(view: ActionView) -> ActionView:
    if view.action_status not in ("DRAFT", "FAILED"):
        raise ValueError(f"Cannot submit from status {view.action_status}")
    if view.is_destructive_external and not view.permission_granted:
        raise ValueError(
            "Cannot submit destructive external action without explicit permission. "
            + DESTRUCTIVE_GUARDRAIL
        )
    return _transition(view, "APPROVAL_REQUIRED", "Submitted for approval.")


def approve_action(view: ActionView, *, comment: str | None = None) -> ActionView:
    if view.action_status != "APPROVAL_REQUIRED":
        raise ValueError(f"Cannot approve from status {view.action_status}")
    if view.is_destructive_external and not view.permission_granted:
        raise ValueError(
            "Cannot approve destructive external action without explicit permission. "
            + DESTRUCTIVE_GUARDRAIL
        )
    reason = "Approved." + (f" {comment}" if comment else "")
    return _transition(view, "APPROVED", reason)


def reject_action(view: ActionView, *, comment: str | None = None) -> ActionView:
    if view.action_status != "APPROVAL_REQUIRED":
        raise ValueError(f"Cannot reject from status {view.action_status}")
    reason = "Rejected; returned to DRAFT." + (f" {comment}" if comment else "")
    return _transition(view, "DRAFT", reason)


def execute_action(view: ActionView, draft: ActionDraft) -> ActionView:
    if view.action_status != "APPROVED":
        raise ValueError(f"Cannot execute from status {view.action_status}")
    if view.is_destructive_external and not view.permission_granted:
        failed = _transition(
            view,
            "FAILED",
            "Execution blocked: missing explicit permission for destructive external modification.",
        )
        exec_result = ExecutionResult(
            outcome="FAILED",
            detail=DESTRUCTIVE_GUARDRAIL,
            external_side_effects=False,
            executor="guardrail",
        )
        failed.executions = [*failed.executions, exec_result]
        failed.failure_reason = DESTRUCTIVE_GUARDRAIL
        return failed

    # Permission scopes that are required but missing (non-destructive connectors)
    scope = view.permission_scope_required
    if scope and not view.permission_granted and view.action_type in (
        "notify_editor",
        "schedule_recrawl",
        "schedule_monitoring",
    ):
        # Still allow internal recording but mark no live external dispatch
        result = _simulate_internal_execution(draft)
        result = ExecutionResult(
            outcome="EXECUTED",
            detail=(
                result.detail
                + f" Note: connector scope '{scope}' not granted — recorded only, "
                "no live external dispatch."
            ),
            external_side_effects=False,
            executor="internal",
        )
    else:
        result = _simulate_internal_execution(draft)

    if result.outcome == "FAILED":
        failed = _transition(view, "FAILED", result.detail)
        failed.executions = [*failed.executions, result]
        failed.failure_reason = result.detail
        return failed

    done = _transition(view, "EXECUTED", result.detail)
    done.executions = [*done.executions, result]
    done.result_summary = result.detail
    done.failure_reason = None
    return done


def revert_action(view: ActionView, *, reason: str = "Reverted by operator.") -> ActionView:
    if view.action_status != "EXECUTED":
        raise ValueError(f"Cannot revert from status {view.action_status}")
    if view.is_destructive_external:
        # Reverting destructive external still requires that we never auto-mutate
        # without permission — record revert intent only
        reverted = _transition(view, "REVERTED", reason + " (external revert is manual/ops).")
    else:
        reverted = _transition(view, "REVERTED", reason)
    reverted.executions = [
        *reverted.executions,
        ExecutionResult(
            outcome="REVERTED",
            detail=reason,
            external_side_effects=False,
            executor="internal",
        ),
    ]
    return reverted


def _transition(view: ActionView, to_status: str, reason: str) -> ActionView:
    if to_status not in ACTION_STATUSES:
        raise ValueError(f"Unknown status {to_status}")
    allowed = ALLOWED_TRANSITIONS.get(view.action_status, frozenset())
    if to_status not in allowed:
        raise ValueError(
            f"Illegal transition {view.action_status} → {to_status}"
        )
    new_transitions = [
        *view.transitions,
        TransitionResult(
            from_status=view.action_status, to_status=to_status, reason=reason
        ),
    ]
    return ActionView(
        action_type=view.action_type,
        action_label=view.action_label,
        title=view.title,
        description=view.description,
        payload_summary=view.payload_summary,
        action_status=to_status,
        requires_approval=view.requires_approval,
        is_destructive_external=view.is_destructive_external,
        permission_scope_required=view.permission_scope_required,
        permission_granted=view.permission_granted,
        risk_level=view.risk_level,
        target_ref=view.target_ref,
        result_summary=view.result_summary,
        failure_reason=view.failure_reason,
        destructive_guardrail=view.destructive_guardrail,
        transitions=new_transitions,
        executions=list(view.executions),
        notes=view.notes,
    )


def catalog() -> dict[str, Any]:
    return {
        "action_types": dict(ACTION_LABELS),
        "action_statuses": list(ACTION_STATUSES),
        "permission_scopes": list(PERMISSION_SCOPES),
        "destructive_external_actions": sorted(DESTRUCTIVE_EXTERNAL_ACTIONS),
        "destructive_guardrail": DESTRUCTIVE_GUARDRAIL,
        "methodology_note": METHODOLOGY_NOTE,
        "status_lifecycle": [
            "DRAFT",
            "APPROVAL_REQUIRED",
            "APPROVED",
            "EXECUTED",
            "FAILED",
            "REVERTED",
        ],
    }
