"""Dynamic model capability profiles API for PINE routing."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_capability import (
    CapabilityCatalogResponse,
    CapabilityObservationRequest,
    CapabilityProfileResponse,
    CapabilityRouteRequest,
    CapabilityRouteResponse,
    ModelRouterRequestSchema,
    ModelRouterResponse,
)
from capability_router import (
    GATEWAY_ROLE_TASK_DEFAULTS,
    SOFT_CAPABILITY_PRIORS,
    CapabilityObservation,
    CapabilityProfileRepository,
    CapabilityRouter,
    CapabilityTaskType,
    ModelRouter,
    ModelRouterRequest,
    OrganisationPolicy,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/capabilities", tags=["capability-profiles"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


@router.get("/catalog", response_model=CapabilityCatalogResponse)
def capability_catalog(ctx: AuthContext = Depends(get_auth_context)) -> CapabilityCatalogResponse:
    return CapabilityCatalogResponse(
        task_types=[t.value for t in CapabilityTaskType],
        soft_priors=[
            {
                "provider_code": p.provider_code,
                "model_code": p.model_code,
                "task_type": p.task_type,
                "quality_score": p.quality_score,
                "notes": p.notes,
                "is_permanent_lock": False,
            }
            for p in SOFT_CAPABILITY_PRIORS
        ],
        gateway_role_task_defaults=dict(GATEWAY_ROLE_TASK_DEFAULTS),
        permanent_role_locks=False,
    )


@router.post("/priors/seed")
def seed_soft_priors(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    created = CapabilityProfileRepository(db).seed_soft_priors()
    return {
        "created_or_refreshed": created,
        "permanent_role_locks": False,
        "message": "Soft priors seeded; observed profiles override them dynamically.",
    }


@router.get("/profiles")
def list_profiles(
    task_type: str | None = Query(default=None),
    workspace_id: str | None = Query(default=None),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    ws = _workspace_id(ctx, workspace_id)
    profiles = CapabilityProfileRepository(db).list_profiles(
        organisation_id=ctx.organisation.id,
        workspace_id=ws,
        task_type=task_type,
    )
    return {
        "profiles": [p.to_dict() for p in profiles],
        "permanent_role_locks": False,
    }


@router.post("/observations", response_model=CapabilityProfileResponse, status_code=201)
def record_observation(
    body: CapabilityObservationRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CapabilityProfileResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        profile = CapabilityProfileRepository(db).record_observation(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            observation=CapabilityObservation(
                provider_code=body.provider_code,
                model_code=body.model_code,
                task_type=body.task_type,
                latency_ms=body.latency_ms,
                cost_usd_micros=body.cost_usd_micros,
                succeeded=body.succeeded,
                quality_score=body.quality_score,
                json_compliant=body.json_compliant,
                citation_accuracy=body.citation_accuracy,
                historical_agreement=body.historical_agreement,
                gateway_role=body.gateway_role,
                template_id=body.template_id,
                llm_request_id=body.llm_request_id,
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="capability.observation",
            resource_type="model_capability_profile",
            resource_id=profile.id or "",
            workspace_id=ws,
            metadata={
                "provider_code": profile.provider_code,
                "model_code": profile.model_code,
                "task_type": str(profile.task_type),
                "sample_size": profile.sample_size,
            },
        )
    )
    return CapabilityProfileResponse(profile=profile.to_dict())


@router.post("/route", response_model=CapabilityRouteResponse)
def route_task(
    body: CapabilityRouteRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CapabilityRouteResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    task_type = body.task_type
    if not task_type and body.gateway_role:
        task_type = CapabilityRouter.task_type_for_gateway_role(body.gateway_role)
    if not task_type:
        raise HTTPException(status_code=400, detail="task_type or gateway_role is required")

    repo = CapabilityProfileRepository(db)
    # Ensure soft priors exist so routing never depends on hardcoded permanent locks alone
    if not repo.list_priors(task_type=task_type):
        repo.seed_soft_priors()

    try:
        decision = CapabilityRouter(repo).route(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            task_type=task_type,
            allowed_providers=set(body.allowed_providers) or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CapabilityRouteResponse(decision=decision.to_dict())


@router.post("/model-router", response_model=ModelRouterResponse)
def model_router_select(
    body: ModelRouterRequestSchema,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ModelRouterResponse:
    """Select primary / secondary / fallback models under full routing constraints."""
    ws = _workspace_id(ctx, body.workspace_id)
    repo = CapabilityProfileRepository(db)
    if not repo.list_priors(task_type=body.task_type):
        repo.seed_soft_priors()

    policy = OrganisationPolicy(
        allowed_providers=body.organisation_policy.allowed_providers,
        denied_providers=body.organisation_policy.denied_providers,
        allowed_models=body.organisation_policy.allowed_models,
        denied_models=body.organisation_policy.denied_models,
        max_cost_usd_micros=body.organisation_policy.max_cost_usd_micros,
        prefer_observed=body.organisation_policy.prefer_observed,
        require_json_capable=body.organisation_policy.require_json_capable,
        prefer_eu_compatible=body.organisation_policy.prefer_eu_compatible,
        notes=body.organisation_policy.notes,
    )
    try:
        result = ModelRouter(CapabilityRouter(repo), session=db).route(
            ModelRouterRequest(
                task_type=body.task_type,
                complexity=body.complexity,
                freshness_requirement=body.freshness_requirement,
                required_capabilities=body.required_capabilities,
                expected_context_size=body.expected_context_size,
                accuracy_requirement=body.accuracy_requirement,
                latency_target=body.latency_target,
                budget=body.budget,
                organisation_policy=policy,
                organisation_id=ctx.organisation.id,
                workspace_id=ws,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="capability.model_router",
            resource_type="model_router_decision",
            resource_id=result.primary_model.key,
            workspace_id=ws,
            metadata={
                "task_type": result.task_type,
                "primary": result.primary_model.key,
                "secondary": result.secondary_model.key if result.secondary_model else None,
                "fallback": result.fallback_model.key if result.fallback_model else None,
            },
        )
    )
    return ModelRouterResponse(**result.to_dict())
