"""Strategic intelligence pipeline API — Layers 0–10 + PINE IntelligenceCase."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_intelligence import (
    IntelligenceCaseResponse,
    IntelligenceCaseUpsertRequest,
    StrategicRunRequest,
    StrategicRunResponse,
)
from db_models.base import new_uuid
from intelligence import (
    CaseAgentFinding,
    CaseAssumption,
    CaseContextItem,
    CaseContradiction,
    CaseEvidence,
    CaseHypothesis,
    CaseModelUsed,
    CaseObservation,
    CaseOpportunity,
    CaseRecommendation,
    CaseRisk,
    CaseToolUsed,
    CaseUnknown,
    IntelligenceCase,
    IntelligenceCaseRepository,
    IntelligenceOrchestrator,
    StrategicRequest,
    list_mode_catalog,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/intelligence", tags=["strategic-intelligence"])
audit_logger = AuditLogger()
_RUNS: dict[str, dict] = {}


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _case_from_request(
    body: IntelligenceCaseUpsertRequest,
    *,
    organisation_id: str,
    workspace_id: str,
) -> IntelligenceCase:
    return IntelligenceCase(
        case_id=body.case_id or new_uuid(),
        organisation_id=organisation_id,
        workspace_id=workspace_id,
        objective=body.objective,
        title=body.title,
        confidence=body.confidence,
        cost_usd_micros=body.cost_usd_micros,
        latency_ms=body.latency_ms,
        website_id=body.website_id,
        strategic_run_id=body.strategic_run_id,
        status=body.status,
        context=[CaseContextItem(**item) for item in body.context],
        observations=[CaseObservation(**item) for item in body.observations],
        evidence=[CaseEvidence(**item) for item in body.evidence],
        hypotheses=[CaseHypothesis(**item) for item in body.hypotheses],
        agent_findings=[CaseAgentFinding(**item) for item in body.agent_findings],
        contradictions=[CaseContradiction(**item) for item in body.contradictions],
        unknowns=[CaseUnknown(**item) for item in body.unknowns],
        assumptions=[CaseAssumption(**item) for item in body.assumptions],
        risks=[CaseRisk(**item) for item in body.risks],
        opportunities=[CaseOpportunity(**item) for item in body.opportunities],
        recommendations=[CaseRecommendation(**item) for item in body.recommendations],
        models_used=[CaseModelUsed(**item) for item in body.models_used],
        tools_used=[CaseToolUsed(**item) for item in body.tools_used],
    )


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
            peacock_mode=body.peacock_mode,
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


@router.get("/modes")
def list_peacock_modes(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    """Catalogue of Peacock Fast / Standard / Deep / Council / Lab modes."""
    modes = list_mode_catalog()
    return {
        "modes": modes,
        "required_budget_fields": ["max_cost", "max_calls", "max_iterations", "max_runtime"],
    }


@router.post("/cases", response_model=IntelligenceCaseResponse, status_code=201)
def upsert_intelligence_case(
    body: IntelligenceCaseUpsertRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> IntelligenceCaseResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    case = _case_from_request(
        body,
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
    )
    saved = IntelligenceCaseRepository(db).save(case)
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="intelligence.case.upsert",
            resource_type="intelligence_case",
            resource_id=saved.case_id,
            workspace_id=workspace_id,
            metadata={
                "evidence": len(saved.evidence),
                "recommendations": len(saved.recommendations),
                "confidence": saved.confidence,
            },
        )
    )
    return IntelligenceCaseResponse(**saved.to_dict())


@router.get("/cases/{case_id}", response_model=IntelligenceCaseResponse)
def get_intelligence_case(
    case_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> IntelligenceCaseResponse:
    case = IntelligenceCaseRepository(db).get(case_id)
    if case is None or case.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Intelligence case not found")
    return IntelligenceCaseResponse(**case.to_dict())
