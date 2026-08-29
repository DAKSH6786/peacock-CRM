"""Prompt Universe Intelligence API — complete intent landscape."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_prompt_universe import (
    CreatePromptUniverseRequest,
    ExpandPromptUniverseRequest,
    PromptUniverseCatalogResponse,
    SyntheticPersonaResponse,
    UniversePromptResponse,
    UniverseSummaryResponse,
)
from observability.audit import AuditEvent, AuditLogger
from prompt_universe import GenerateUniverseSpec, PromptUniverseService, SourceSignalSpec

router = APIRouter(prefix="/prompt-universe", tags=["prompt-universe-intelligence"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _summary_response(summary) -> UniverseSummaryResponse:
    return UniverseSummaryResponse(
        universe_id=summary.universe_id,
        name=summary.name,
        brand_name=summary.brand_name,
        generation_status=summary.generation_status,
        prompt_count=summary.prompt_count,
        family_count=summary.family_count,
        signal_count=summary.signal_count,
        persona_count=summary.persona_count,
        prompt_type_counts=summary.prompt_type_counts,
        simple_count=summary.simple_count,
        contextual_count=summary.contextual_count,
        tracks_both_simple_and_contextual=True,
    )


@router.get("/catalog", response_model=PromptUniverseCatalogResponse)
def prompt_universe_catalog(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> PromptUniverseCatalogResponse:
    _ = ctx
    return PromptUniverseCatalogResponse(**PromptUniverseService(db).catalog())


@router.post("/universes", response_model=UniverseSummaryResponse, status_code=201)
def create_prompt_universe(
    body: CreatePromptUniverseRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UniverseSummaryResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        summary = PromptUniverseService(db).create_and_generate(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=GenerateUniverseSpec(
                website_id=body.website_id,
                name=body.name,
                brand_name=body.brand_name,
                industry=body.industry,
                primary_location=body.primary_location,
                description=body.description,
                notes=body.notes,
                signals=[SourceSignalSpec(**s.model_dump()) for s in body.signals],
                persona_codes=body.persona_codes,
                include_persona_variants=body.include_persona_variants,
                max_prompts=body.max_prompts,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="prompt_universe.create",
            resource_type="prompt_universe",
            resource_id=summary.universe_id,
            workspace_id=ws,
            metadata={
                "prompt_count": summary.prompt_count,
                "family_count": summary.family_count,
                "simple_count": summary.simple_count,
                "contextual_count": summary.contextual_count,
            },
        )
    )
    return _summary_response(summary)


@router.get("/universes/{universe_id}", response_model=UniverseSummaryResponse)
def get_prompt_universe(
    universe_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UniverseSummaryResponse:
    try:
        summary = PromptUniverseService(db).summarise(universe_id, ctx.organisation.id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _summary_response(summary)


@router.post("/universes/{universe_id}/expand", response_model=UniverseSummaryResponse)
def expand_prompt_universe(
    universe_id: str,
    body: ExpandPromptUniverseRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> UniverseSummaryResponse:
    try:
        summary = PromptUniverseService(db).add_signals_and_expand(
            universe_id=universe_id,
            organisation_id=ctx.organisation.id,
            signals=[SourceSignalSpec(**s.model_dump()) for s in body.signals],
            include_persona_variants=body.include_persona_variants,
            max_new_prompts=body.max_new_prompts,
            created_by=ctx.user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="prompt_universe.expand",
            resource_type="prompt_universe",
            resource_id=universe_id,
            workspace_id=ctx.workspace.id if ctx.workspace else None,
            metadata={"signals": len(body.signals)},
        )
    )
    return _summary_response(summary)


@router.get("/universes/{universe_id}/prompts", response_model=list[UniversePromptResponse])
def list_universe_prompts(
    universe_id: str,
    prompt_type: str | None = None,
    persona_code: str | None = None,
    complexity: str | None = Query(default=None, description="simple|contextual"),
    tracked_only: bool = False,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[UniversePromptResponse]:
    try:
        rows = PromptUniverseService(db).list_prompts(
            universe_id=universe_id,
            organisation_id=ctx.organisation.id,
            prompt_type=prompt_type,
            persona_code=persona_code,
            complexity=complexity,
            tracked_only=tracked_only,
            limit=limit,
            offset=offset,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return [
        UniversePromptResponse(
            id=r.id,
            prompt_text=r.prompt_text,
            topic=r.topic,
            subtopic=r.subtopic,
            intent=r.intent,
            persona=r.persona_code,
            funnel_stage=r.funnel_stage,
            location=r.location,
            product=r.product,
            problem=r.problem,
            commercial_value=r.commercial_value,
            brand_relevance=r.brand_relevance,
            prompt_type=r.prompt_type,
            source_kind=r.source_kind,
            complexity=r.complexity,
            is_tracked=r.is_tracked,
            priority=r.priority,
            family_id=r.family_id,
        )
        for r in rows
    ]


@router.get("/universes/{universe_id}/personas", response_model=list[SyntheticPersonaResponse])
def list_universe_personas(
    universe_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[SyntheticPersonaResponse]:
    try:
        rows = PromptUniverseService(db).list_personas(
            universe_id=universe_id,
            organisation_id=ctx.organisation.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        SyntheticPersonaResponse(
            code=r.code,
            name=r.name,
            description=r.description,
            query_style=r.query_style,
            is_system_seed=r.is_system_seed,
        )
        for r in rows
    ]
