"""Peacock Research Mode API — controlled laboratory studies."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from research_mode import (
    ObservationSpec,
    PageSpec,
    PromptSpec,
    ResearchModeCreateSpec,
    ResearchModeService,
    ResearchStudySpec,
    analyse_research_study,
    catalog,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_research_mode import (
    FindingResponse,
    ObservationResponse,
    PageResponse,
    PromptResponse,
    ResearchModeCatalogResponse,
    ResearchModePreviewResponse,
    ResearchStudyCreateRequest,
    ResearchStudyResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/research-mode", tags=["research-mode"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _result_fields(result) -> dict:
    return {
        "research_question": result.research_question,
        "hypothesis": result.hypothesis,
        "metric_key": result.metric_key,
        "metric_label": result.metric_label,
        "treatment_description": result.treatment_description,
        "completed_phases": result.completed_phases,
        "pages": [PageResponse(**p.to_dict()) for p in result.pages],
        "prompts": [PromptResponse(**p.to_dict()) for p in result.prompts],
        "observations": [ObservationResponse(**o.to_dict()) for o in result.observations],
        "findings": [FindingResponse(**f.to_dict()) for f in result.findings],
        "baseline_mean": result.baseline_mean,
        "treatment_mean": result.treatment_mean,
        "absolute_delta": result.absolute_delta,
        "relative_delta_pct": result.relative_delta_pct,
        "control_adjusted_delta": result.control_adjusted_delta,
        "uncertainty_band": result.uncertainty_band,
        "uncertainty_score": result.uncertainty_score,
        "finding_verdict": result.finding_verdict,
        "finding_summary": result.finding_summary,
        "observation_rounds": result.observation_rounds,
        "pages_count": result.pages_count,
        "prompts_count": result.prompts_count,
        "laboratory_positioning": result.laboratory_positioning,
        "causality_warning": result.causality_warning,
        "methodology_note": result.methodology_note,
        "analysed_at": result.analysed_at.isoformat(),
    }


def _to_response(report) -> ResearchStudyResponse:
    return ResearchStudyResponse(
        study_id=report.study_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_result_fields(report.result),
    )


@router.get("/catalog", response_model=ResearchModeCatalogResponse)
def research_mode_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> ResearchModeCatalogResponse:
    _ = ctx
    return ResearchModeCatalogResponse(**catalog())


@router.get("/preview", response_model=ResearchModePreviewResponse)
def research_mode_preview(brand: str = "Acme") -> ResearchModePreviewResponse:
    """Public demo study for the example research question."""
    result = analyse_research_study(
        ResearchStudySpec(
            client_brand=brand,
            research_question=(
                "Does adding proprietary statistics increase AI citation probability?"
            ),
            hypothesis=(
                "Adding proprietary statistics to treatment pages increases AI "
                "citation probability versus baseline on selected prompts."
            ),
            metric_key="ai_citation_probability",
            treatment_description="Add proprietary statistics blocks to treatment pages.",
            observation_rounds=3,
        )
    )
    return ResearchModePreviewResponse(
        client_brand=result.client_brand,
        **_result_fields(result),
    )


@router.post("/studies", response_model=ResearchStudyResponse, status_code=201)
def create_research_study(
    body: ResearchStudyCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ResearchStudyResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ResearchModeService(db).run_study(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=ResearchModeCreateSpec(
                website_id=body.website_id,
                name=body.name,
                study=ResearchStudySpec(
                    client_brand=body.brief.client_brand,
                    research_question=body.brief.research_question,
                    hypothesis=body.brief.hypothesis,
                    metric_key=body.brief.metric_key,
                    treatment_description=body.brief.treatment_description,
                    pages=[
                        PageSpec(url=p.url, page_role=p.page_role, label=p.label)
                        for p in body.brief.pages
                    ],
                    prompts=[
                        PromptSpec(
                            prompt_text=p.prompt_text,
                            prompt_cluster=p.prompt_cluster,
                        )
                        for p in body.brief.prompts
                    ],
                    observations=[
                        ObservationSpec(
                            arm=o.arm,
                            round_index=o.round_index,
                            page_url=o.page_url,
                            page_role=o.page_role,
                            prompt_text=o.prompt_text,
                            value=o.value,
                            observed_at=o.observed_at,
                        )
                        for o in body.brief.observations
                    ],
                    observation_rounds=body.brief.observation_rounds,
                    analysed_at=body.brief.analysed_at,
                ),
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="research_mode.study",
            resource_type="research_study",
            resource_id=report.study_id,
            workspace_id=ws,
            metadata={
                "finding_verdict": report.result.finding_verdict,
                "uncertainty_band": report.result.uncertainty_band,
                "metric_key": report.result.metric_key,
            },
        )
    )
    return _to_response(report)


@router.get("/studies/{study_id}", response_model=ResearchStudyResponse)
def get_research_study(
    study_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ResearchStudyResponse:
    report = ResearchModeService(db).get_study(
        study_id=study_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Research study not found")
    return _to_response(report)
