"""Peacock Action Engine API — approval-based execution."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from action_engine import (
    ActionDraft,
    ActionEngineService,
    ActionEngineSpec,
    catalog,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_action_engine import (
    ActionCatalogResponse,
    ActionResponse,
    ApprovalRequest,
    CreateActionRequest,
    ExecutionResponse,
    GrantPermissionRequest,
    PermissionResponse,
    RevertRequest,
    TransitionResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/actions", tags=["actions"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> ActionResponse:
    v = report.view
    return ActionResponse(
        action_id=report.action_id,
        methodology=report.methodology,
        action_type=v.action_type,
        action_label=v.action_label,
        title=v.title,
        description=v.description,
        payload_summary=v.payload_summary,
        action_status=v.action_status,
        requires_approval=v.requires_approval,
        is_destructive_external=v.is_destructive_external,
        permission_scope_required=v.permission_scope_required,
        permission_granted=v.permission_granted,
        risk_level=v.risk_level,
        target_ref=v.target_ref,
        result_summary=v.result_summary,
        failure_reason=v.failure_reason,
        destructive_guardrail=v.destructive_guardrail,
        transitions=[TransitionResponse(**t.to_dict()) for t in v.transitions],
        executions=[ExecutionResponse(**e.to_dict()) for e in v.executions],
        notes=v.notes,
    )


@router.get("/catalog", response_model=ActionCatalogResponse)
def actions_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> ActionCatalogResponse:
    _ = ctx
    return ActionCatalogResponse(**catalog())


@router.post("", response_model=ActionResponse, status_code=201)
def create_action(
    body: CreateActionRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ActionResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ActionEngineService(db).create(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=ActionEngineSpec(
                website_id=body.website_id,
                draft=ActionDraft(**body.draft.model_dump()),
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="action_engine.create",
            resource_type="peacock_action",
            resource_id=report.action_id,
            workspace_id=ws,
            metadata={
                "action_type": report.view.action_type,
                "action_status": report.view.action_status,
                "is_destructive_external": report.view.is_destructive_external,
            },
        )
    )
    return _to_response(report)


@router.get("/{action_id}", response_model=ActionResponse)
def get_action(
    action_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ActionResponse:
    report = ActionEngineService(db).get(
        action_id=action_id, organisation_id=ctx.organisation.id
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Action not found")
    return _to_response(report)


@router.post("/{action_id}/submit", response_model=ActionResponse)
def submit_action(
    action_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ActionResponse:
    try:
        report = ActionEngineService(db).submit(
            action_id=action_id,
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="action_engine.submit",
            resource_type="peacock_action",
            resource_id=action_id,
            metadata={"action_status": report.view.action_status},
        )
    )
    return _to_response(report)


@router.post("/{action_id}/approve", response_model=ActionResponse)
def approve_action_route(
    action_id: str,
    body: ApprovalRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ActionResponse:
    try:
        report = ActionEngineService(db).approve(
            action_id=action_id,
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            comment=body.comment,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="action_engine.approve",
            resource_type="peacock_action",
            resource_id=action_id,
            metadata={"action_status": report.view.action_status},
        )
    )
    return _to_response(report)


@router.post("/{action_id}/reject", response_model=ActionResponse)
def reject_action_route(
    action_id: str,
    body: ApprovalRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ActionResponse:
    try:
        report = ActionEngineService(db).reject(
            action_id=action_id,
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            comment=body.comment,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(report)


@router.post("/{action_id}/execute", response_model=ActionResponse)
def execute_action_route(
    action_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ActionResponse:
    try:
        report = ActionEngineService(db).execute(
            action_id=action_id,
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="action_engine.execute",
            resource_type="peacock_action",
            resource_id=action_id,
            metadata={
                "action_status": report.view.action_status,
                "is_destructive_external": report.view.is_destructive_external,
            },
        )
    )
    return _to_response(report)


@router.post("/{action_id}/revert", response_model=ActionResponse)
def revert_action_route(
    action_id: str,
    body: RevertRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ActionResponse:
    try:
        report = ActionEngineService(db).revert(
            action_id=action_id,
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            reason=body.reason,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(report)


@router.post("/permissions/grant", response_model=PermissionResponse, status_code=201)
def grant_permission(
    body: GrantPermissionRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PermissionResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    row = ActionEngineService(db).grant_permission(
        organisation_id=ctx.organisation.id,
        workspace_id=ws,
        connector=body.connector,
        permission_scope=body.permission_scope,
        granted_by=ctx.user.id,
        website_id=body.website_id,
        notes=body.notes,
    )
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="action_engine.grant_permission",
            resource_type="pae_connector_permission",
            resource_id=row.id,
            workspace_id=ws,
            metadata={
                "connector": row.connector,
                "permission_scope": row.permission_scope,
            },
        )
    )
    return PermissionResponse(
        permission_id=row.id,
        connector=row.connector,
        permission_scope=row.permission_scope,
        granted=row.granted,
    )
