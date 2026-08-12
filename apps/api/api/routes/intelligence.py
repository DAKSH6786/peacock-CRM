"""Strategic intelligence pipeline API — Layers 0–10."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import AuthContext, get_auth_context
from api.schemas_intelligence import StrategicRunRequest, StrategicRunResponse
from intelligence import IntelligenceOrchestrator, StrategicRequest
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/intelligence", tags=["strategic-intelligence"])
audit_logger = AuditLogger()
_RUNS: dict[str, dict] = {}


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


@router.post("/runs", response_model=StrategicRunResponse, status_code=201)
async def create_strategic_run(
    body: StrategicRunRequest,
    ctx: AuthContext = Depends(get_auth_context),
) -> StrategicRunResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    orchestrator = IntelligenceOrchestrator(organisation_id=ctx.organisation.id)
    result = await orchestrator.run_strategy(
        StrategicRequest(
            organisation_id=ctx.organisation.id,
            workspace_id=workspace_id,
            request_text=body.request_text,
            website_id=body.website_id,
            crawl_id=body.crawl_id,
            audit_id=body.audit_id,
            requested_output=body.requested_output,
            metadata=body.metadata,
        )
    )
    payload = result.to_dict()
    _RUNS[result.id] = payload
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="intelligence.run",
            resource_type="strategic_run",
            resource_id=result.id,
            workspace_id=workspace_id,
            metadata={
                "intent": result.classification.user_intent,
                "layers": len(result.layers),
                "recommendations": len(result.recommendations),
            },
        )
    )
    return StrategicRunResponse(**payload)


@router.get("/runs/{run_id}", response_model=StrategicRunResponse)
def get_strategic_run(
    run_id: str,
    ctx: AuthContext = Depends(get_auth_context),
) -> StrategicRunResponse:
    payload = _RUNS.get(run_id)
    if payload is None or payload.get("organisation_id") != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Strategic run not found")
    return StrategicRunResponse(**payload)


@router.get("/layers")
def list_layers(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    return IntelligenceOrchestrator(ctx.organisation.id).status()
