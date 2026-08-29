"""Proprietary Metrics orchestration — persist documented scorecards."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.proprietary_metrics import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    PmMetricComponent,
    PmMetricScore,
    ProprietaryMetricScorecard,
)
from proprietary_metrics.formulas import MetricComputation
from proprietary_metrics.models import ProprietaryMetricsCreateSpec, ProprietaryMetricsReport
from proprietary_metrics.scoring import ProprietaryMetricsResult, score_proprietary_metrics


class ProprietaryMetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_scorecard(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: ProprietaryMetricsCreateSpec,
        created_by: str | None = None,
    ) -> ProprietaryMetricsReport:
        result = score_proprietary_metrics(spec.scorecard)

        card = ProprietaryMetricScorecard(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            scorecard_status="completed",
            methodology=METHODOLOGY,
            scored_at=result.scored_at,
            metrics_scored=result.metrics_scored,
            proprietary_disclaimer=result.proprietary_disclaimer,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(card)
        self.db.flush()

        for i, m in enumerate(result.metrics):
            row = PmMetricScore(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                scorecard_id=card.id,
                metric_key=m.metric_key,
                metric_label=m.metric_label,
                score=m.score,
                unit=m.unit,
                formula_id=m.formula_id,
                formula_text=m.formula_text,
                explanation=m.explanation,
                proprietary_note=m.proprietary_note,
                rank_order=i,
            )
            self.db.add(row)
            self.db.flush()
            for c in m.components:
                self.db.add(
                    PmMetricComponent(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        metric_score_id=row.id,
                        component_key=c["component_key"],
                        component_label=c["component_label"],
                        raw_value=c["raw_value"],
                        weight=c["weight"],
                        contribution=c["contribution"],
                        rank_order=c["rank_order"],
                    )
                )

        self.db.commit()
        return ProprietaryMetricsReport(
            scorecard_id=card.id,
            name=card.name,
            client_brand=card.client_brand,
            methodology=card.methodology,
            result=result,
        )

    def get_scorecard(
        self, *, scorecard_id: str, organisation_id: str
    ) -> ProprietaryMetricsReport | None:
        card = self.db.scalar(
            select(ProprietaryMetricScorecard).where(
                ProprietaryMetricScorecard.id == scorecard_id,
                ProprietaryMetricScorecard.organisation_id == organisation_id,
            )
        )
        if card is None:
            return None

        metrics: list[MetricComputation] = []
        for row in self.db.scalars(
            select(PmMetricScore)
            .where(PmMetricScore.scorecard_id == card.id)
            .order_by(PmMetricScore.rank_order.asc())
        ).all():
            comps = [
                {
                    "component_key": c.component_key,
                    "component_label": c.component_label,
                    "raw_value": c.raw_value,
                    "weight": c.weight,
                    "contribution": c.contribution,
                    "rank_order": c.rank_order,
                }
                for c in self.db.scalars(
                    select(PmMetricComponent)
                    .where(PmMetricComponent.metric_score_id == row.id)
                    .order_by(PmMetricComponent.rank_order.asc())
                ).all()
            ]
            metrics.append(
                MetricComputation(
                    metric_key=row.metric_key,
                    metric_label=row.metric_label,
                    score=row.score,
                    unit=row.unit,
                    formula_id=row.formula_id,
                    formula_text=row.formula_text,
                    explanation=row.explanation,
                    proprietary_note=row.proprietary_note,
                    components=comps,
                )
            )

        result = ProprietaryMetricsResult(
            client_brand=card.client_brand,
            scored_at=card.scored_at,
            metrics=metrics,
            metrics_scored=card.metrics_scored,
            proprietary_disclaimer=card.proprietary_disclaimer,
            methodology_note=METHODOLOGY_NOTE,
            summary=card.summary or "",
        )
        return ProprietaryMetricsReport(
            scorecard_id=card.id,
            name=card.name,
            client_brand=card.client_brand,
            methodology=card.methodology,
            result=result,
        )
