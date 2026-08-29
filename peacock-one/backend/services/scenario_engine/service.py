"""Peacock Scenario Engine orchestration — counterfactual strategy comparison."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.scenario_engine import (
    METHODOLOGY,
    RANGES_NOT_FAKE_PRECISION,
    ScenarioAnalysis,
    SeAssumption,
    SeMetricRange,
    SeScenario,
)
from scenario_engine.models import ScenarioEngineReport, ScenarioEngineSpec
from scenario_engine.projections import (
    AssumptionResult,
    MetricRangeResult,
    ScenarioAnalysisResult,
    ScenarioResult,
    run_scenario_analysis,
)


class ScenarioEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: ScenarioEngineSpec,
        created_by: str | None = None,
    ) -> ScenarioEngineReport:
        result = run_scenario_analysis(spec.scenario)

        analysis = ScenarioAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.scenario.client_brand.strip(),
            horizon_days=result.horizon_days,
            primary_metric=result.primary_metric,
            primary_metric_label=result.primary_metric_label,
            analysis_status="completed",
            methodology=METHODOLOGY,
            ranges_not_fake_precision=True,
            ranges_disclaimer=RANGES_NOT_FAKE_PRECISION,
            overall_data_quality=result.overall_data_quality,
            overall_uncertainty=result.overall_uncertainty,
            overall_confidence=result.overall_confidence,
            assumptions_summary=result.assumptions_summary,
            recommended_strategy_code=result.recommended_strategy_code,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        for s in result.scenarios:
            row = SeScenario(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                analysis_id=analysis.id,
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
            )
            self.db.add(row)
            self.db.flush()
            for m in s.metric_ranges:
                self.db.add(
                    SeMetricRange(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        scenario_id=row.id,
                        metric_code=m.metric_code,
                        metric_label=m.metric_label,
                        range_low_pct=m.range_low_pct,
                        range_high_pct=m.range_high_pct,
                        unit=m.unit,
                    )
                )

        for a in result.assumptions:
            self.db.add(
                SeAssumption(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    assumption_key=a.assumption_key,
                    statement=a.statement,
                    sensitivity=a.sensitivity,
                    affects_strategies=",".join(a.affects_strategies),
                )
            )

        self.db.commit()
        return ScenarioEngineReport(
            analysis_id=analysis.id,
            name=analysis.name,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            result=result,
        )

    def get_analysis(
        self, *, analysis_id: str, organisation_id: str
    ) -> ScenarioEngineReport | None:
        analysis = self.db.scalar(
            select(ScenarioAnalysis).where(
                ScenarioAnalysis.id == analysis_id,
                ScenarioAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        scenario_rows = list(
            self.db.scalars(
                select(SeScenario)
                .where(SeScenario.analysis_id == analysis.id)
                .order_by(SeScenario.rank.asc())
            ).all()
        )
        scenarios: list[ScenarioResult] = []
        for s in scenario_rows:
            metrics = [
                MetricRangeResult(
                    metric_code=m.metric_code,
                    metric_label=m.metric_label,
                    range_low_pct=m.range_low_pct,
                    range_high_pct=m.range_high_pct,
                    unit=m.unit,
                )
                for m in self.db.scalars(
                    select(SeMetricRange).where(SeMetricRange.scenario_id == s.id)
                ).all()
            ]
            scenarios.append(
                ScenarioResult(
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
                    metric_ranges=metrics,
                    display_band=f"{s.range_low_pct:+.0f}% to {s.range_high_pct:+.0f}%",
                )
            )

        assumptions = [
            AssumptionResult(
                assumption_key=a.assumption_key,
                statement=a.statement,
                sensitivity=a.sensitivity,
                affects_strategies=[
                    x for x in (a.affects_strategies or "").split(",") if x
                ],
            )
            for a in self.db.scalars(
                select(SeAssumption).where(SeAssumption.analysis_id == analysis.id)
            ).all()
        ]

        from db_models.scenario_engine import METHODOLOGY_NOTE

        comparison_table = [
            {"strategy": s.strategy_label, "projected_range": s.display_band}
            for s in scenarios
        ]
        result = ScenarioAnalysisResult(
            horizon_days=analysis.horizon_days,
            primary_metric=analysis.primary_metric,
            primary_metric_label=analysis.primary_metric_label,
            scenarios=scenarios,
            assumptions=assumptions,
            overall_confidence=analysis.overall_confidence,
            overall_data_quality=analysis.overall_data_quality,
            overall_uncertainty=analysis.overall_uncertainty,
            assumptions_summary=analysis.assumptions_summary,
            ranges_not_fake_precision=analysis.ranges_not_fake_precision,
            ranges_disclaimer=analysis.ranges_disclaimer,
            methodology_note=METHODOLOGY_NOTE,
            recommended_strategy_code=analysis.recommended_strategy_code
            or "peacock_recommended",
            comparison_table=comparison_table,
            summary=analysis.summary or "",
        )
        return ScenarioEngineReport(
            analysis_id=analysis.id,
            name=analysis.name,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            result=result,
        )
