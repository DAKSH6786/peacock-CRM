"""Revenue Attribution orchestration — persist uncertain funnel chains."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.revenue_attribution import (
    CAUSALITY_WARNING,
    METHODOLOGY,
    RaChainLink,
    RaFunnelStage,
    RaSourceSnapshot,
    RevenueAttributionAnalysis,
)
from revenue_attribution.attribution import (
    AttributionAnalysisResult,
    ChainLinkResult,
    SourceSnapshotResult,
    StageResult,
    attribute_revenue,
)
from revenue_attribution.models import RevenueAttributionReport, RevenueAttributionSpec


class RevenueAttributionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: RevenueAttributionSpec,
        created_by: str | None = None,
    ) -> RevenueAttributionReport:
        result = attribute_revenue(spec.attribution)

        analysis = RevenueAttributionAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.attribution.client_brand.strip(),
            currency=result.currency,
            horizon_days=result.horizon_days,
            analysis_status="completed",
            methodology=METHODOLOGY,
            causality_warning=CAUSALITY_WARNING,
            overall_causality_level=result.overall_causality_level,
            overall_uncertainty=result.overall_uncertainty,
            data_completeness=result.data_completeness,
            attributed_revenue_low=result.attributed_revenue_low,
            attributed_revenue_high=result.attributed_revenue_high,
            attributed_revenue_mid=result.attributed_revenue_mid,
            sources_available=",".join(result.sources_available),
            sources_missing=",".join(result.sources_missing),
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        for s in result.stages:
            self.db.add(
                RaFunnelStage(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    stage_code=s.stage_code,
                    stage_label=s.stage_label,
                    sequence_order=s.sequence_order,
                    value_low=s.value_low,
                    value_high=s.value_high,
                    value_mid=s.value_mid,
                    unit=s.unit,
                    uncertainty=s.uncertainty,
                    data_quality=s.data_quality,
                    primary_source=s.primary_source,
                    notes=s.notes,
                )
            )

        for link in result.links:
            self.db.add(
                RaChainLink(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    from_stage=link.from_stage,
                    to_stage=link.to_stage,
                    rate_low=link.rate_low,
                    rate_high=link.rate_high,
                    causality_level=link.causality_level,
                    uncertainty=link.uncertainty,
                    rationale=link.rationale,
                )
            )

        for snap in result.source_snapshots:
            self.db.add(
                RaSourceSnapshot(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    source_code=snap.source_code,
                    source_label=snap.source_label,
                    available=snap.available,
                    contribution_note=snap.contribution_note,
                )
            )

        self.db.commit()
        return RevenueAttributionReport(
            analysis_id=analysis.id,
            name=analysis.name,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            result=result,
        )

    def get_analysis(
        self, *, analysis_id: str, organisation_id: str
    ) -> RevenueAttributionReport | None:
        analysis = self.db.scalar(
            select(RevenueAttributionAnalysis).where(
                RevenueAttributionAnalysis.id == analysis_id,
                RevenueAttributionAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        stages = [
            StageResult(
                stage_code=s.stage_code,
                stage_label=s.stage_label,
                sequence_order=s.sequence_order,
                value_low=s.value_low,
                value_high=s.value_high,
                value_mid=s.value_mid,
                unit=s.unit,
                uncertainty=s.uncertainty,
                data_quality=s.data_quality,
                primary_source=s.primary_source,
                notes=s.notes,
                display_band=(
                    f"{s.value_low:,.0f}–{s.value_high:,.0f} {s.unit}"
                    if s.stage_code == "revenue"
                    else f"{s.value_low:,.1f}–{s.value_high:,.1f} {s.unit}"
                ),
            )
            for s in self.db.scalars(
                select(RaFunnelStage)
                .where(RaFunnelStage.analysis_id == analysis.id)
                .order_by(RaFunnelStage.sequence_order.asc())
            ).all()
        ]
        links = [
            ChainLinkResult(
                from_stage=l.from_stage,
                to_stage=l.to_stage,
                rate_low=l.rate_low,
                rate_high=l.rate_high,
                causality_level=l.causality_level,
                uncertainty=l.uncertainty,
                rationale=l.rationale,
            )
            for l in self.db.scalars(
                select(RaChainLink).where(RaChainLink.analysis_id == analysis.id)
            ).all()
        ]
        snaps = [
            SourceSnapshotResult(
                source_code=s.source_code,
                source_label=s.source_label,
                available=s.available,
                contribution_note=s.contribution_note,
            )
            for s in self.db.scalars(
                select(RaSourceSnapshot).where(
                    RaSourceSnapshot.analysis_id == analysis.id
                )
            ).all()
        ]
        from db_models.revenue_attribution import METHODOLOGY_NOTE, STAGE_LABELS

        result = AttributionAnalysisResult(
            currency=analysis.currency,
            horizon_days=analysis.horizon_days,
            stages=stages,
            links=links,
            source_snapshots=snaps,
            attributed_revenue_low=analysis.attributed_revenue_low,
            attributed_revenue_high=analysis.attributed_revenue_high,
            attributed_revenue_mid=analysis.attributed_revenue_mid,
            overall_causality_level=analysis.overall_causality_level,
            overall_uncertainty=analysis.overall_uncertainty,
            data_completeness=analysis.data_completeness,
            causality_warning=analysis.causality_warning,
            methodology_note=METHODOLOGY_NOTE,
            sources_available=[
                x for x in analysis.sources_available.split(",") if x
            ],
            sources_missing=[x for x in analysis.sources_missing.split(",") if x],
            funnel_path=[STAGE_LABELS[s.stage_code] for s in stages],
            summary=analysis.summary or "",
        )
        return RevenueAttributionReport(
            analysis_id=analysis.id,
            name=analysis.name,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            result=result,
        )
