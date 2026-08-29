"""Peacock Action Engine orchestration — persist approval-gated actions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from action_engine.models import ActionEngineReport, ActionEngineSpec
from action_engine.workflow import (
    ActionDraft,
    ActionView,
    ExecutionResult,
    TransitionResult,
    approve_action,
    create_action_view,
    execute_action,
    reject_action,
    revert_action,
    submit_for_approval,
)
from db_models.action_engine import (
    DESTRUCTIVE_GUARDRAIL,
    METHODOLOGY,
    PaeApproval,
    PaeConnectorPermission,
    PaeExecution,
    PaeStatusEvent,
    PeacockAction,
)
from db_models.base import new_uuid


class ActionEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _granted_scopes(
        self, *, organisation_id: str, workspace_id: str
    ) -> list[str]:
        rows = self.db.scalars(
            select(PaeConnectorPermission).where(
                PaeConnectorPermission.organisation_id == organisation_id,
                PaeConnectorPermission.workspace_id == workspace_id,
                PaeConnectorPermission.granted.is_(True),
            )
        ).all()
        return [r.permission_scope for r in rows]

    def _persist_new(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        website_id: str,
        view: ActionView,
        created_by: str | None,
        notes: str | None,
    ) -> PeacockAction:
        action = PeacockAction(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=website_id,
            action_type=view.action_type,
            action_label=view.action_label,
            title=view.title,
            description=view.description,
            payload_summary=view.payload_summary,
            action_status=view.action_status,
            requires_approval=view.requires_approval,
            is_destructive_external=view.is_destructive_external,
            permission_scope_required=view.permission_scope_required,
            permission_granted=view.permission_granted,
            risk_level=view.risk_level,
            target_ref=view.target_ref,
            result_summary=view.result_summary,
            failure_reason=view.failure_reason,
            methodology=METHODOLOGY,
            destructive_guardrail=DESTRUCTIVE_GUARDRAIL,
            notes=notes,
        )
        self.db.add(action)
        self.db.flush()
        self._append_events(
            action=action,
            view=view,
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            prior_transition_count=0,
            prior_execution_count=0,
        )
        self.db.commit()
        return action

    def _append_events(
        self,
        *,
        action: PeacockAction,
        view: ActionView,
        organisation_id: str,
        workspace_id: str,
        created_by: str | None,
        prior_transition_count: int,
        prior_execution_count: int,
    ) -> None:
        for t in view.transitions[prior_transition_count:]:
            self.db.add(
                PaeStatusEvent(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    action_id=action.id,
                    from_status=t.from_status,
                    to_status=t.to_status,
                    reason=t.reason,
                    actor_user_id=created_by,
                )
            )
        for idx, e in enumerate(
            view.executions[prior_execution_count:], start=prior_execution_count + 1
        ):
            self.db.add(
                PaeExecution(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    action_id=action.id,
                    attempt_number=idx,
                    outcome=e.outcome,
                    executor=e.executor,
                    detail=e.detail,
                    external_side_effects=e.external_side_effects,
                )
            )

    def _load_view(self, action: PeacockAction) -> ActionView:
        transitions = [
            TransitionResult(
                from_status=e.from_status,
                to_status=e.to_status,
                reason=e.reason,
            )
            for e in self.db.scalars(
                select(PaeStatusEvent)
                .where(PaeStatusEvent.action_id == action.id)
                .order_by(PaeStatusEvent.created_at.asc())
            ).all()
        ]
        executions = [
            ExecutionResult(
                outcome=e.outcome,
                detail=e.detail,
                external_side_effects=e.external_side_effects,
                executor=e.executor,
            )
            for e in self.db.scalars(
                select(PaeExecution)
                .where(PaeExecution.action_id == action.id)
                .order_by(PaeExecution.attempt_number.asc())
            ).all()
        ]
        return ActionView(
            action_type=action.action_type,
            action_label=action.action_label,
            title=action.title,
            description=action.description,
            payload_summary=action.payload_summary,
            action_status=action.action_status,
            requires_approval=action.requires_approval,
            is_destructive_external=action.is_destructive_external,
            permission_scope_required=action.permission_scope_required,
            permission_granted=action.permission_granted,
            risk_level=action.risk_level,
            target_ref=action.target_ref,
            result_summary=action.result_summary,
            failure_reason=action.failure_reason,
            destructive_guardrail=action.destructive_guardrail,
            transitions=transitions,
            executions=executions,
            notes=action.notes,
        )

    def _save_view(
        self,
        action: PeacockAction,
        view: ActionView,
        *,
        actor_user_id: str | None,
        prior_transition_count: int,
        prior_execution_count: int,
        approval_decision: str | None = None,
        approval_comment: str | None = None,
    ) -> ActionEngineReport:
        action.action_status = view.action_status
        action.permission_granted = view.permission_granted
        action.result_summary = view.result_summary
        action.failure_reason = view.failure_reason
        self._append_events(
            action=action,
            view=view,
            organisation_id=action.organisation_id,
            workspace_id=action.workspace_id,
            created_by=actor_user_id,
            prior_transition_count=prior_transition_count,
            prior_execution_count=prior_execution_count,
        )
        if approval_decision:
            self.db.add(
                PaeApproval(
                    id=new_uuid(),
                    organisation_id=action.organisation_id,
                    workspace_id=action.workspace_id,
                    created_by=actor_user_id,
                    action_id=action.id,
                    decision=approval_decision,
                    decided_by=actor_user_id,
                    comment=approval_comment,
                )
            )
        self.db.commit()
        return ActionEngineReport(
            action_id=action.id, methodology=action.methodology, view=view
        )

    def create(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: ActionEngineSpec,
        created_by: str | None = None,
    ) -> ActionEngineReport:
        granted = list(spec.granted_permissions or [])
        granted.extend(
            self._granted_scopes(
                organisation_id=organisation_id, workspace_id=workspace_id
            )
        )
        view = create_action_view(spec.draft, granted_permissions=granted)
        action = self._persist_new(
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            website_id=spec.website_id,
            view=view,
            created_by=created_by,
            notes=spec.draft.notes,
        )
        return ActionEngineReport(
            action_id=action.id, methodology=action.methodology, view=view
        )

    def get(
        self, *, action_id: str, organisation_id: str
    ) -> ActionEngineReport | None:
        action = self.db.scalar(
            select(PeacockAction).where(
                PeacockAction.id == action_id,
                PeacockAction.organisation_id == organisation_id,
            )
        )
        if action is None:
            return None
        return ActionEngineReport(
            action_id=action.id,
            methodology=action.methodology,
            view=self._load_view(action),
        )

    def submit(self, *, action_id: str, organisation_id: str, actor_user_id: str | None) -> ActionEngineReport:
        action = self._require(action_id, organisation_id)
        view = self._load_view(action)
        prior_t, prior_e = len(view.transitions), len(view.executions)
        # Refresh permission from grants
        scopes = self._granted_scopes(
            organisation_id=organisation_id, workspace_id=action.workspace_id
        )
        view.permission_granted = (
            view.permission_scope_required is None
            or view.permission_scope_required in scopes
        )
        action.permission_granted = view.permission_granted
        new_view = submit_for_approval(view)
        return self._save_view(
            action,
            new_view,
            actor_user_id=actor_user_id,
            prior_transition_count=prior_t,
            prior_execution_count=prior_e,
        )

    def approve(
        self,
        *,
        action_id: str,
        organisation_id: str,
        actor_user_id: str | None,
        comment: str | None = None,
    ) -> ActionEngineReport:
        action = self._require(action_id, organisation_id)
        view = self._load_view(action)
        prior_t, prior_e = len(view.transitions), len(view.executions)
        scopes = self._granted_scopes(
            organisation_id=organisation_id, workspace_id=action.workspace_id
        )
        view.permission_granted = (
            view.permission_scope_required is None
            or view.permission_scope_required in scopes
        )
        action.permission_granted = view.permission_granted
        new_view = approve_action(view, comment=comment)
        return self._save_view(
            action,
            new_view,
            actor_user_id=actor_user_id,
            prior_transition_count=prior_t,
            prior_execution_count=prior_e,
            approval_decision="approve",
            approval_comment=comment,
        )

    def reject(
        self,
        *,
        action_id: str,
        organisation_id: str,
        actor_user_id: str | None,
        comment: str | None = None,
    ) -> ActionEngineReport:
        action = self._require(action_id, organisation_id)
        view = self._load_view(action)
        prior_t, prior_e = len(view.transitions), len(view.executions)
        new_view = reject_action(view, comment=comment)
        return self._save_view(
            action,
            new_view,
            actor_user_id=actor_user_id,
            prior_transition_count=prior_t,
            prior_execution_count=prior_e,
            approval_decision="reject",
            approval_comment=comment,
        )

    def execute(
        self, *, action_id: str, organisation_id: str, actor_user_id: str | None
    ) -> ActionEngineReport:
        action = self._require(action_id, organisation_id)
        view = self._load_view(action)
        prior_t, prior_e = len(view.transitions), len(view.executions)
        scopes = self._granted_scopes(
            organisation_id=organisation_id, workspace_id=action.workspace_id
        )
        view.permission_granted = (
            view.permission_scope_required is None
            or view.permission_scope_required in scopes
        )
        action.permission_granted = view.permission_granted
        draft = ActionDraft(
            action_type=action.action_type,
            title=action.title,
            payload_summary=action.payload_summary,
            description=action.description,
            target_ref=action.target_ref,
            risk_level=action.risk_level,
            requires_approval=action.requires_approval,
            notes=action.notes,
        )
        new_view = execute_action(view, draft)
        return self._save_view(
            action,
            new_view,
            actor_user_id=actor_user_id,
            prior_transition_count=prior_t,
            prior_execution_count=prior_e,
        )

    def revert(
        self,
        *,
        action_id: str,
        organisation_id: str,
        actor_user_id: str | None,
        reason: str = "Reverted by operator.",
    ) -> ActionEngineReport:
        action = self._require(action_id, organisation_id)
        view = self._load_view(action)
        prior_t, prior_e = len(view.transitions), len(view.executions)
        new_view = revert_action(view, reason=reason)
        return self._save_view(
            action,
            new_view,
            actor_user_id=actor_user_id,
            prior_transition_count=prior_t,
            prior_execution_count=prior_e,
        )

    def grant_permission(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        connector: str,
        permission_scope: str,
        granted_by: str | None,
        website_id: str | None = None,
        notes: str | None = None,
    ) -> PaeConnectorPermission:
        existing = self.db.scalar(
            select(PaeConnectorPermission).where(
                PaeConnectorPermission.workspace_id == workspace_id,
                PaeConnectorPermission.permission_scope == permission_scope,
                PaeConnectorPermission.connector == connector,
            )
        )
        if existing:
            existing.granted = True
            existing.granted_by = granted_by
            existing.notes = notes
            existing.website_id = website_id
            self.db.commit()
            return existing
        row = PaeConnectorPermission(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=granted_by,
            website_id=website_id,
            connector=connector,
            permission_scope=permission_scope,
            granted=True,
            granted_by=granted_by,
            notes=notes,
        )
        self.db.add(row)
        self.db.commit()
        return row

    def _require(self, action_id: str, organisation_id: str) -> PeacockAction:
        action = self.db.scalar(
            select(PeacockAction).where(
                PeacockAction.id == action_id,
                PeacockAction.organisation_id == organisation_id,
            )
        )
        if action is None:
            raise LookupError("Action not found")
        return action
