"""Peacock Proprietary Metrics API — documented scoring framework."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from proprietary_metrics import (
    MetricInputs,
    ProprietaryMetricsCreateSpec,
    ProprietaryMetricsService,
    ProprietaryMetricsSpec,
    catalog,
    score_proprietary_metrics,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_proprietary_metrics import (
    MetricComponentResponse,
    MetricScoreResponse,
    ProprietaryMetricsCatalogResponse,
    ProprietaryMetricsCreateRequest,
    ProprietaryMetricsPreviewResponse,
    ProprietaryMetricsResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/proprietary-metrics", tags=["proprietary-metrics"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _metrics_payload(result) -> dict:
    return {
        "scored_at": result.scored_at.isoformat(),
        "metrics_scored": result.metrics_scored,
        "proprietary_disclaimer": result.proprietary_disclaimer,
        "methodology_note": result.methodology_note,
        "summary": result.summary,
        "metrics": [
            MetricScoreResponse(
                metric_key=m.metric_key,
                metric_label=m.metric_label,
                score=m.score,
                unit=m.unit,
                formula_id=m.formula_id,
                formula_text=m.formula_text,
                explanation=m.explanation,
                proprietary_note=m.proprietary_note,
                components=[MetricComponentResponse(**c) for c in m.components],
            )
            for m in result.metrics
        ],
        "not_official_platforms": list(result.to_dict()["not_official_platforms"]),
    }


def _to_response(report) -> ProprietaryMetricsResponse:
    return ProprietaryMetricsResponse(
        scorecard_id=report.scorecard_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_metrics_payload(report.result),
    )


@router.get("/catalog", response_model=ProprietaryMetricsCatalogResponse)
def proprietary_metrics_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> ProprietaryMetricsCatalogResponse:
    _ = ctx
    return ProprietaryMetricsCatalogResponse(**catalog())


@router.get("/preview", response_model=ProprietaryMetricsPreviewResponse)
def proprietary_metrics_preview(brand: str = "Acme") -> ProprietaryMetricsPreviewResponse:
    """Public demo scorecard with every formula attached."""
    result = score_proprietary_metrics(ProprietaryMetricsSpec(client_brand=brand))
    return ProprietaryMetricsPreviewResponse(
        client_brand=result.client_brand,
        **_metrics_payload(result),
    )


@router.post("/scorecards", response_model=ProprietaryMetricsResponse, status_code=201)
def create_proprietary_scorecard(
    body: ProprietaryMetricsCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ProprietaryMetricsResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ProprietaryMetricsService(db).create_scorecard(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=ProprietaryMetricsCreateSpec(
                website_id=body.website_id,
                name=body.name,
                scorecard=ProprietaryMetricsSpec(
                    client_brand=body.brief.client_brand,
                    inputs=MetricInputs(**body.brief.inputs.model_dump()),
                    scored_at=body.brief.scored_at,
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
            action="proprietary_metrics.score",
            resource_type="proprietary_metric_scorecard",
            resource_id=report.scorecard_id,
            workspace_id=ws,
            metadata={"metrics_scored": report.result.metrics_scored},
        )
    )
    return _to_response(report)


@router.get("/scorecards/{scorecard_id}", response_model=ProprietaryMetricsResponse)
def get_proprietary_scorecard(
    scorecard_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ProprietaryMetricsResponse:
    report = ProprietaryMetricsService(db).get_scorecard(
        scorecard_id=scorecard_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Proprietary metrics scorecard not found")
    return _to_response(report)
