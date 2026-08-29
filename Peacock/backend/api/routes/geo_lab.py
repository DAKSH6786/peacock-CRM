"""Peacock GEO Lab API — controlled GEO experimentation with causality warning."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_geo_lab import (
    CausalityAssessmentResponse,
    GeoLabCatalogResponse,
    GeoLabExperimentRequest,
    GeoLabExperimentResponse,
    MetricDeltaResponse,
    TimeSeriesPointResponse,
)
from geo_lab import (
    CAUSALITY_LEVELS,
    CAUSALITY_WARNING,
    GEO_LAB_METRICS,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    PAGE_ROLES,
    VARIANT_CODES,
    VARIANT_PRESETS,
    GeoLabService,
    GeoLabSpec,
    ObservationSpec,
    PageSpec,
    VariantSpec,
)
from geo_lab.analysis import ExperimentAnalysisInput, analyse_experiment, default_variants
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/geo-lab", tags=["geo-lab"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> GeoLabExperimentResponse:
    return GeoLabExperimentResponse(
        experiment_id=report.experiment_id,
        name=report.name,
        client_brand=report.client_brand,
        hypothesis=report.hypothesis,
        methodology=report.methodology,
        design_type=report.design_type,
        design_features=report.design_features,
        causality_warning=report.causality_warning,
        overall_causality_level=report.overall_causality_level,
        overall_summary=report.overall_summary,
        auto_causal_conclusion_rejected=True,
        variants=report.variants,
        pages=report.pages,
        deltas=[MetricDeltaResponse(**d.to_dict()) for d in report.deltas],
        causality_assessments=[
            CausalityAssessmentResponse(**c.to_dict())
            for c in report.causality_assessments
        ],
        time_series=[TimeSeriesPointResponse(**t.to_dict()) for t in report.time_series],
    )


@router.get("/preview", response_model=GeoLabExperimentResponse)
def geo_lab_preview(brand: str = "Acme") -> GeoLabExperimentResponse:
    """Public demo GEO Lab experiment for the Website SEO/AEO/GEO Audit module."""
    control_url = f"https://{brand.lower()}.example.com/blog/industry-overview"
    test_url = f"https://{brand.lower()}.example.com/guides/benchmarks"
    pages = [
        PageSpec(url=control_url, page_role="control", title="Industry overview (control)"),
        PageSpec(
            url=test_url,
            page_role="test",
            variant_code="D",
            title="Benchmarks hub (treatment)",
            matched_group="benchmarks_vs_overview",
        ),
    ]
    observations = [
        ObservationSpec(page_url=control_url, metric_code="ai_citation", observed_at="2024-05-01", period="pre", value=0.18),
        ObservationSpec(page_url=control_url, metric_code="ai_citation", observed_at="2024-06-01", period="post", value=0.2),
        ObservationSpec(page_url=test_url, metric_code="ai_citation", observed_at="2024-05-01", period="pre", value=0.21),
        ObservationSpec(page_url=test_url, metric_code="ai_citation", observed_at="2024-06-01", period="post", value=0.34),
    ]
    analysis = analyse_experiment(
        ExperimentAnalysisInput(
            variants=default_variants(),
            pages=pages,
            observations=observations,
        )
    )
    return GeoLabExperimentResponse(
        experiment_id="preview",
        name=f"{brand} — Original dataset GEO experiment (preview)",
        client_brand=brand,
        hypothesis="Publishing an original benchmarks dataset increases AI citation probability.",
        methodology=METHODOLOGY,
        design_type="before_after_with_controls",
        design_features=analysis.design_features,
        causality_warning=analysis.causality_warning,
        overall_causality_level=analysis.overall_causality_level,
        overall_summary=analysis.overall_summary,
        auto_causal_conclusion_rejected=True,
        variants=[v.to_dict() for v in default_variants()],
        pages=[p.to_dict() for p in pages],
        deltas=[MetricDeltaResponse(**d.to_dict()) for d in analysis.deltas],
        causality_assessments=[
            CausalityAssessmentResponse(**c.to_dict()) for c in analysis.causality_assessments
        ],
        time_series=[TimeSeriesPointResponse(**t.to_dict()) for t in analysis.time_series],
    )


@router.get("/catalog", response_model=GeoLabCatalogResponse)
def geo_lab_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> GeoLabCatalogResponse:
    _ = ctx
    return GeoLabCatalogResponse(
        variant_presets=dict(VARIANT_PRESETS),
        variant_codes=list(VARIANT_CODES),
        metrics=list(GEO_LAB_METRICS),
        page_roles=list(PAGE_ROLES),
        causality_levels=list(CAUSALITY_LEVELS),
        causality_warning=CAUSALITY_WARNING,
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
    )


@router.post("/experiments", response_model=GeoLabExperimentResponse, status_code=201)
def create_geo_lab_experiment(
    body: GeoLabExperimentRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> GeoLabExperimentResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = GeoLabService(db).run_experiment(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=GeoLabSpec(
                website_id=body.website_id,
                name=body.name,
                client_brand=body.client_brand,
                hypothesis=body.hypothesis,
                topic_cluster=body.topic_cluster,
                design_type=body.design_type,
                pre_window_start=body.pre_window_start,
                pre_window_end=body.pre_window_end,
                post_window_start=body.post_window_start,
                post_window_end=body.post_window_end,
                intervention_date=body.intervention_date,
                variants=[
                    VariantSpec(**v.model_dump()) for v in body.variants
                ],
                pages=[PageSpec(**p.model_dump()) for p in body.pages],
                observations=[
                    ObservationSpec(**o.model_dump()) for o in body.observations
                ],
                known_confounds=body.known_confounds,
                concurrent_changes=body.concurrent_changes,
                notes=body.notes,
                use_default_variants_if_empty=body.use_default_variants_if_empty,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="geo_lab.experiment",
            resource_type="geo_lab_experiment",
            resource_id=report.experiment_id,
            workspace_id=ws,
            metadata={
                "overall_causality_level": report.overall_causality_level,
                "auto_causal_conclusion_rejected": True,
                "design_features": report.design_features,
            },
        )
    )
    return _to_response(report)


@router.get("/experiments/{experiment_id}", response_model=GeoLabExperimentResponse)
def get_geo_lab_experiment(
    experiment_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> GeoLabExperimentResponse:
    report = GeoLabService(db).get_experiment(
        experiment_id=experiment_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="GEO Lab experiment not found")
    return _to_response(report)
