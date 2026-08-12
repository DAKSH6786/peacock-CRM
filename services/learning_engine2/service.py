"""Learning Engine 2.0 orchestration — persist closed-loop learning."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.learning_engine2 import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    NOT_UNIVERSAL_GEO,
    Le2ContextFactor,
    Le2DimensionInsight,
    Le2IndustryPolicy,
    Le2LearningRun,
    Learning2Record,
)
from learning_engine2.learning import (
    ContextFactorResult,
    ExecutionUpdate,
    IndustryPolicyResult,
    LearningRecordView,
    LearningRunResult,
    OutcomeUpdate,
    apply_execution,
    apply_outcome,
    learn_from_records,
)
from learning_engine2.models import (
    Learning2CreateSpec,
    Learning2RecordReport,
    Learning2RunReport,
)


class LearningEngine2Service:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_record(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: Learning2CreateSpec,
        created_by: str | None = None,
    ) -> Learning2RecordReport:
        view = spec.view
        row = Learning2Record(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            central_recommendation_id=spec.central_recommendation_id,
            name=view.name,
            industry=view.industry,
            record_status=view.record_status,
            context_summary=view.context_summary,
            recommendation_text=view.recommendation_text,
            expected_impact=view.expected_impact,
            expected_impact_score=view.expected_impact_score,
            confidence=view.confidence,
            topic_key=view.topic_key,
            format_key=view.format_key,
            source_key=view.source_key,
            writer_key=view.writer_key,
            intervention_key=view.intervention_key,
            engine_key=view.engine_key,
            methodology=METHODOLOGY,
            not_universal_geo_strategy=True,
            not_universal_geo_note=NOT_UNIVERSAL_GEO,
            notes=spec.notes,
        )
        self.db.add(row)
        self.db.flush()
        for f in view.context_factors:
            self.db.add(
                Le2ContextFactor(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    record_id=row.id,
                    factor_key=f.factor_key,
                    factor_value=f.factor_value,
                    weight=f.weight,
                )
            )
        self.db.commit()
        return Learning2RecordReport(
            record_id=row.id, methodology=row.methodology, view=view
        )

    def _load_view(self, row: Learning2Record) -> LearningRecordView:
        factors = [
            ContextFactorResult(
                factor_key=f.factor_key,
                factor_value=f.factor_value,
                weight=f.weight,
            )
            for f in self.db.scalars(
                select(Le2ContextFactor).where(Le2ContextFactor.record_id == row.id)
            ).all()
        ]
        return LearningRecordView(
            name=row.name,
            industry=row.industry,
            record_status=row.record_status,
            context_summary=row.context_summary,
            recommendation_text=row.recommendation_text,
            expected_impact=row.expected_impact,
            expected_impact_score=row.expected_impact_score,
            confidence=row.confidence,
            execution_summary=row.execution_summary,
            execution_status=row.execution_status,
            actual_outcome=row.actual_outcome,
            actual_outcome_score=row.actual_outcome_score,
            outcome_delta=row.outcome_delta,
            topic_key=row.topic_key,
            format_key=row.format_key,
            source_key=row.source_key,
            writer_key=row.writer_key,
            intervention_key=row.intervention_key,
            engine_key=row.engine_key,
            context_factors=factors,
            not_universal_geo_strategy=row.not_universal_geo_strategy,
            not_universal_geo_note=row.not_universal_geo_note,
        )

    def get_record(
        self, *, record_id: str, organisation_id: str
    ) -> Learning2RecordReport | None:
        row = self.db.scalar(
            select(Learning2Record).where(
                Learning2Record.id == record_id,
                Learning2Record.organisation_id == organisation_id,
            )
        )
        if row is None:
            return None
        return Learning2RecordReport(
            record_id=row.id,
            methodology=row.methodology,
            view=self._load_view(row),
        )

    def record_execution(
        self,
        *,
        record_id: str,
        organisation_id: str,
        update: ExecutionUpdate,
    ) -> Learning2RecordReport:
        row = self._require(record_id, organisation_id)
        view = apply_execution(self._load_view(row), update)
        row.execution_summary = view.execution_summary
        row.execution_status = view.execution_status
        row.record_status = view.record_status
        self.db.commit()
        return Learning2RecordReport(
            record_id=row.id, methodology=row.methodology, view=view
        )

    def record_outcome(
        self,
        *,
        record_id: str,
        organisation_id: str,
        update: OutcomeUpdate,
    ) -> Learning2RecordReport:
        row = self._require(record_id, organisation_id)
        view = apply_outcome(self._load_view(row), update)
        row.actual_outcome = view.actual_outcome
        row.actual_outcome_score = view.actual_outcome_score
        row.outcome_delta = view.outcome_delta
        row.record_status = view.record_status
        self.db.commit()
        return Learning2RecordReport(
            record_id=row.id, methodology=row.methodology, view=view
        )

    def run_learning(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        name: str,
        website_id: str | None = None,
        created_by: str | None = None,
    ) -> Learning2RunReport:
        q = select(Learning2Record).where(
            Learning2Record.organisation_id == organisation_id,
            Learning2Record.workspace_id == workspace_id,
        )
        if website_id:
            q = q.where(Learning2Record.website_id == website_id)
        rows = list(self.db.scalars(q).all())
        views = [self._load_view(r) for r in rows]
        result = learn_from_records(views)

        # Upsert insights
        for insight in result.insights:
            existing = self.db.scalar(
                select(Le2DimensionInsight).where(
                    Le2DimensionInsight.organisation_id == organisation_id,
                    Le2DimensionInsight.dimension == insight.dimension,
                    Le2DimensionInsight.dimension_key == insight.dimension_key,
                    Le2DimensionInsight.industry == insight.industry,
                )
            )
            if existing:
                existing.sample_size = insight.sample_size
                existing.avg_expected_impact = insight.avg_expected_impact
                existing.avg_actual_outcome = insight.avg_actual_outcome
                existing.avg_confidence = insight.avg_confidence
                existing.success_rate = insight.success_rate
                existing.insight_summary = insight.insight_summary
                existing.workspace_id = workspace_id
            else:
                self.db.add(
                    Le2DimensionInsight(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        dimension=insight.dimension,
                        dimension_key=insight.dimension_key,
                        industry=insight.industry,
                        sample_size=insight.sample_size,
                        avg_expected_impact=insight.avg_expected_impact,
                        avg_actual_outcome=insight.avg_actual_outcome,
                        avg_confidence=insight.avg_confidence,
                        success_rate=insight.success_rate,
                        insight_summary=insight.insight_summary,
                        not_universal_geo_strategy=True,
                    )
                )

        for policy in result.industry_policies:
            existing = self.db.scalar(
                select(Le2IndustryPolicy).where(
                    Le2IndustryPolicy.organisation_id == organisation_id,
                    Le2IndustryPolicy.industry == policy.industry,
                    Le2IndustryPolicy.policy_code == policy.policy_code,
                )
            )
            if existing:
                existing.title = policy.title
                existing.guidance = policy.guidance
                existing.preferred_formats = ",".join(policy.preferred_formats)
                existing.preferred_sources = ",".join(policy.preferred_sources)
                existing.citation_interventions = ",".join(
                    policy.citation_interventions
                )
                existing.forbidden_universal_claims = policy.forbidden_universal_claims
                existing.sample_size = policy.sample_size
                existing.success_rate = policy.success_rate
                existing.active = policy.active
                existing.workspace_id = workspace_id
            else:
                self.db.add(
                    Le2IndustryPolicy(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        industry=policy.industry,
                        policy_code=policy.policy_code,
                        title=policy.title,
                        guidance=policy.guidance,
                        preferred_formats=",".join(policy.preferred_formats),
                        preferred_sources=",".join(policy.preferred_sources),
                        citation_interventions=",".join(policy.citation_interventions),
                        forbidden_universal_claims=policy.forbidden_universal_claims,
                        active=True,
                        sample_size=policy.sample_size,
                        success_rate=policy.success_rate,
                    )
                )

        for row in rows:
            if row.record_status == "outcome_recorded":
                row.record_status = "learned"

        run = Le2LearningRun(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=website_id,
            name=name,
            records_considered=result.records_considered,
            insights_generated=len(result.insights),
            industries_touched=",".join(result.industries_touched),
            not_universal_geo_strategy=True,
            methodology_note=METHODOLOGY_NOTE,
            summary=result.summary,
        )
        self.db.add(run)
        self.db.commit()
        return Learning2RunReport(
            run_id=run.id,
            name=run.name,
            methodology=METHODOLOGY,
            result=result,
        )

    def list_policies(
        self, *, organisation_id: str, workspace_id: str
    ) -> list[IndustryPolicyResult]:
        from db_models.learning_engine2 import INDUSTRY_LABELS

        rows = list(
            self.db.scalars(
                select(Le2IndustryPolicy).where(
                    Le2IndustryPolicy.organisation_id == organisation_id,
                    Le2IndustryPolicy.workspace_id == workspace_id,
                    Le2IndustryPolicy.active.is_(True),
                )
            ).all()
        )
        if not rows:
            return []
        return [
            IndustryPolicyResult(
                industry=r.industry,
                industry_label=INDUSTRY_LABELS.get(r.industry, r.industry),
                policy_code=r.policy_code,
                title=r.title,
                guidance=r.guidance,
                preferred_formats=[x for x in (r.preferred_formats or "").split(",") if x],
                preferred_sources=[x for x in (r.preferred_sources or "").split(",") if x],
                citation_interventions=[
                    x for x in (r.citation_interventions or "").split(",") if x
                ],
                forbidden_universal_claims=r.forbidden_universal_claims,
                sample_size=r.sample_size,
                success_rate=r.success_rate,
                active=r.active,
            )
            for r in rows
        ]

    def _require(self, record_id: str, organisation_id: str) -> Learning2Record:
        row = self.db.scalar(
            select(Learning2Record).where(
                Learning2Record.id == record_id,
                Learning2Record.organisation_id == organisation_id,
            )
        )
        if row is None:
            raise LookupError("Learning record not found")
        return row
