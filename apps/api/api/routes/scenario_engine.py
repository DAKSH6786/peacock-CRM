"""Peacock Scenario Engine API — counterfactual strategy ranges."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_scenario_engine import (
    AssumptionResponse,
    MetricRangeResponse,
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse,
    ScenarioCatalogResponse,
    ScenarioResponse,
)
from observability.audit import AuditEvent, AuditLogger
from scenario_engine import (
    DEFAULT_METRIC,
    DEFAULT_METRIC_LABEL,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    RANGES_NOT_FAKE_PRECISION,
    STRATEGY_CODES,
    STRATEGY_LABELS,
    AssumptionInput,
    ContextSignals,
    ScenarioEngineService,
    ScenarioEngineSpec,
    ScenarioSpec,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> ScenarioAnalysisResponse:
    r = report.result
    return ScenarioAnalysisResponse(
        analysis_id=report.analysis_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        horizon_days=r.horizon_days,
        primary_metric=r.primary_metric,
        primary_metric_label=r.primary_metric_label,
        ranges_not_fake_precision=True,
        ranges_disclaimer=r.ranges_disclaimer,
        methodology_note=r.methodology_note,
        overall_confidence=r.overall_confidence,
        overall_data_quality=r.overall_data_quality,
        overall_uncertainty=r.overall_uncertainty,
        assumptions_summary=r.assumptions_summary,
        recommended_strategy_code=r.recommended_strategy_code,
        comparison_table=r.comparison_table,
        scenarios=[
            ScenarioResponse(
                strategy_code=s.strategy_code,
                strategy_label=s.strategy_label,
                is_baseline=s.is_baseline,
                is_peacock_recommended=s.is_peacock_recommended,
                range_low_pct=s.range_low_pct,
                range_high_pct=s.range_high_pct,
                range_mid_pct=s.range_mid_pct,
                confidence=s.confidence,
                data_quality=s.data_quality,
                uncertainty=s.uncertainty,
                rationale=s.rationale,
                rank=s.rank,
                metric_ranges=[MetricRangeResponse(**m.to_dict()) for m in s.metric_ranges],
                display_band=s.display_band,
            )
            for s in r.scenarios
        ],
        assumptions=[AssumptionResponse(**a.to_dict()) for a in r.assumptions],
        summary=r.summary,
    )


@router.get("/catalog", response_model=ScenarioCatalogResponse)
def scenarios_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> ScenarioCatalogResponse:
    _ = ctx
    return ScenarioCatalogResponse(
        strategies=dict(STRATEGY_LABELS),
        strategy_codes=list(STRATEGY_CODES),
        default_metric=DEFAULT_METRIC,
        default_metric_label=DEFAULT_METRIC_LABEL,
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
        ranges_not_fake_precision=True,
        ranges_disclaimer=RANGES_NOT_FAKE_PRECISION,
        example_comparison=[
            {"strategy": "Baseline", "projected_range": "+0% to +4%"},
            {"strategy": "Content Expansion", "projected_range": "+7% to +18%"},
            {"strategy": "Authority Strategy", "projected_range": "+9% to +22%"},
            {"strategy": "Peacock Strategy", "projected_range": "+14% to +31%"},
        ],
    )


@router.post("/analyses", response_model=ScenarioAnalysisResponse, status_code=201)
def create_scenario_analysis(
    body: ScenarioAnalysisRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ScenarioAnalysisResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ScenarioEngineService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=ScenarioEngineSpec(
                website_id=body.website_id,
                name=body.name,
                scenario=ScenarioSpec(
                    client_brand=body.brief.client_brand,
                    horizon_days=body.brief.horizon_days,
                    primary_metric=body.brief.primary_metric,
                    primary_metric_label=body.brief.primary_metric_label,
                    context=ContextSignals(**body.brief.context.model_dump()),
                    assumptions=[
                        AssumptionInput(**a.model_dump()) for a in body.brief.assumptions
                    ],
                    strategies=list(body.brief.strategies),
                    extra_metrics=[
                        (m.metric_code, m.metric_label) for m in body.brief.extra_metrics
                    ],
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
            action="scenario_engine.analyse",
            resource_type="scenario_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "ranges_not_fake_precision": True,
                "scenarios": len(report.result.scenarios),
                "recommended": report.result.recommended_strategy_code,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=ScenarioAnalysisResponse)
def get_scenario_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ScenarioAnalysisResponse:
    report = ScenarioEngineService(db).get_analysis(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Scenario analysis not found")
    return _to_response(report)
