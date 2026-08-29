"""Content Digital Twin orchestration — create, modify plan, rerun evaluation."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from content_digital_twin.models import TwinEvaluationReport, TwinReport, TwinSpec
from content_digital_twin.simulation import (
    ArticlePlan,
    FindingResult,
    RequirementScoreResult,
    SimulationContext,
    TwinSimulationResult,
    simulate_article_plan,
)
from db_models.base import new_uuid
from db_models.content_digital_twin import (
    METHODOLOGY,
    CdtEvaluation,
    CdtFinding,
    CdtRequirementScore,
    ContentDigitalTwin,
)


class ContentDigitalTwinService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_twin(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: TwinSpec,
        created_by: str | None = None,
    ) -> TwinReport:
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")
        if not spec.article_plan.title.strip():
            raise ValueError("article_plan.title is required")

        twin = ContentDigitalTwin(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.client_brand.strip(),
            topic_cluster=spec.topic_cluster,
            twin_status="active",
            article_plan_json=json.dumps(spec.article_plan.to_dict()),
            simulation_context_json=json.dumps(spec.simulation_context.to_dict()),
            plan_revision=1,
            evaluation_count=0,
            content_lab_proposal_id=spec.content_lab_proposal_id,
            methodology=METHODOLOGY,
            notes=spec.notes,
        )
        self.db.add(twin)
        self.db.flush()

        evaluation = self._run_evaluation(
            twin=twin,
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            plan=spec.article_plan,
            context=spec.simulation_context,
        )
        twin.latest_evaluation_id = evaluation.id
        twin.evaluation_count = 1
        twin.twin_status = "evaluated"
        self.db.commit()
        return self.get_twin(twin_id=twin.id, organisation_id=organisation_id)  # type: ignore[return-value]

    def update_plan(
        self,
        *,
        twin_id: str,
        organisation_id: str,
        article_plan: ArticlePlan | None = None,
        simulation_context: SimulationContext | None = None,
        name: str | None = None,
        notes: str | None = None,
        rerun: bool = True,
        created_by: str | None = None,
    ) -> TwinReport:
        twin = self._get_twin_row(twin_id, organisation_id)
        if twin is None:
            raise ValueError("Content Digital Twin not found")

        plan = (
            article_plan
            if article_plan is not None
            else ArticlePlan.from_dict(json.loads(twin.article_plan_json))
        )
        context = (
            simulation_context
            if simulation_context is not None
            else SimulationContext.from_dict(json.loads(twin.simulation_context_json))
        )
        if not plan.title.strip():
            raise ValueError("article_plan.title is required")

        twin.article_plan_json = json.dumps(plan.to_dict())
        twin.simulation_context_json = json.dumps(context.to_dict())
        twin.plan_revision = int(twin.plan_revision) + 1
        if name:
            twin.name = name
        if notes is not None:
            twin.notes = notes
        twin.twin_status = "plan_updated"
        self.db.flush()

        if rerun:
            evaluation = self._run_evaluation(
                twin=twin,
                organisation_id=organisation_id,
                workspace_id=twin.workspace_id,
                created_by=created_by,
                plan=plan,
                context=context,
            )
            twin.latest_evaluation_id = evaluation.id
            twin.evaluation_count = int(twin.evaluation_count) + 1
            twin.twin_status = "evaluated"

        self.db.commit()
        return self.get_twin(twin_id=twin.id, organisation_id=organisation_id)  # type: ignore[return-value]

    def rerun_evaluation(
        self,
        *,
        twin_id: str,
        organisation_id: str,
        created_by: str | None = None,
    ) -> TwinReport:
        twin = self._get_twin_row(twin_id, organisation_id)
        if twin is None:
            raise ValueError("Content Digital Twin not found")

        plan = ArticlePlan.from_dict(json.loads(twin.article_plan_json))
        context = SimulationContext.from_dict(json.loads(twin.simulation_context_json))
        evaluation = self._run_evaluation(
            twin=twin,
            organisation_id=organisation_id,
            workspace_id=twin.workspace_id,
            created_by=created_by,
            plan=plan,
            context=context,
        )
        twin.latest_evaluation_id = evaluation.id
        twin.evaluation_count = int(twin.evaluation_count) + 1
        twin.twin_status = "evaluated"
        self.db.commit()
        return self.get_twin(twin_id=twin.id, organisation_id=organisation_id)  # type: ignore[return-value]

    def get_twin(self, *, twin_id: str, organisation_id: str) -> TwinReport | None:
        twin = self._get_twin_row(twin_id, organisation_id)
        if twin is None:
            return None

        evals = list(
            self.db.scalars(
                select(CdtEvaluation)
                .where(
                    CdtEvaluation.twin_id == twin.id,
                    CdtEvaluation.organisation_id == organisation_id,
                )
                .order_by(CdtEvaluation.evaluation_number.desc())
            ).all()
        )
        latest: TwinEvaluationReport | None = None
        history: list[dict] = []
        for ev in evals:
            report = self._evaluation_to_report(twin, ev)
            history.append(
                {
                    "evaluation_id": ev.id,
                    "evaluation_number": ev.evaluation_number,
                    "plan_revision": ev.plan_revision,
                    "predicted_strength_score": ev.predicted_strength_score,
                    "readiness_score": ev.readiness_score,
                    "summary": ev.summary,
                }
            )
            if latest is None:
                latest = report

        return TwinReport(
            twin_id=twin.id,
            name=twin.name,
            client_brand=twin.client_brand,
            methodology=twin.methodology,
            plan_revision=twin.plan_revision,
            evaluation_count=twin.evaluation_count,
            article_plan=ArticlePlan.from_dict(json.loads(twin.article_plan_json)),
            simulation_context=SimulationContext.from_dict(
                json.loads(twin.simulation_context_json)
            ),
            latest_evaluation=latest,
            evaluation_history=history,
        )

    def get_evaluation(
        self, *, twin_id: str, evaluation_id: str, organisation_id: str
    ) -> TwinEvaluationReport | None:
        twin = self._get_twin_row(twin_id, organisation_id)
        if twin is None:
            return None
        ev = self.db.scalar(
            select(CdtEvaluation).where(
                CdtEvaluation.id == evaluation_id,
                CdtEvaluation.twin_id == twin_id,
                CdtEvaluation.organisation_id == organisation_id,
            )
        )
        if ev is None:
            return None
        return self._evaluation_to_report(twin, ev)

    def _get_twin_row(
        self, twin_id: str, organisation_id: str
    ) -> ContentDigitalTwin | None:
        return self.db.scalar(
            select(ContentDigitalTwin).where(
                ContentDigitalTwin.id == twin_id,
                ContentDigitalTwin.organisation_id == organisation_id,
            )
        )

    def _run_evaluation(
        self,
        *,
        twin: ContentDigitalTwin,
        organisation_id: str,
        workspace_id: str,
        created_by: str | None,
        plan: ArticlePlan,
        context: SimulationContext,
    ) -> CdtEvaluation:
        result: TwinSimulationResult = simulate_article_plan(plan, context)
        next_num = int(twin.evaluation_count) + 1

        evaluation = CdtEvaluation(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            twin_id=twin.id,
            evaluation_number=next_num,
            plan_revision=twin.plan_revision,
            article_plan_snapshot_json=json.dumps(plan.to_dict()),
            simulation_context_snapshot_json=json.dumps(context.to_dict()),
            predicted_strength_score=result.predicted_strength_score,
            readiness_score=result.readiness_score,
            summary=result.summary,
            evaluation_status="completed",
        )
        self.db.add(evaluation)
        self.db.flush()

        for rs in result.requirement_scores:
            self.db.add(
                CdtRequirementScore(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    evaluation_id=evaluation.id,
                    surface=rs.surface,
                    coverage_score=rs.coverage_score,
                    matched_count=rs.matched_count,
                    missing_count=rs.missing_count,
                    explanation=rs.explanation,
                )
            )

        for finding in result.findings:
            self.db.add(
                CdtFinding(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    evaluation_id=evaluation.id,
                    category=finding.category,
                    title=finding.title,
                    detail=finding.detail,
                    severity=finding.severity,
                    related_surface=finding.related_surface,
                    related_item=finding.related_item,
                    priority=finding.priority,
                )
            )

        self.db.flush()
        return evaluation

    def _evaluation_to_report(
        self, twin: ContentDigitalTwin, ev: CdtEvaluation
    ) -> TwinEvaluationReport:
        req_rows = list(
            self.db.scalars(
                select(CdtRequirementScore).where(
                    CdtRequirementScore.evaluation_id == ev.id
                )
            ).all()
        )
        finding_rows = list(
            self.db.scalars(
                select(CdtFinding)
                .where(CdtFinding.evaluation_id == ev.id)
                .order_by(CdtFinding.priority.desc())
            ).all()
        )
        requirement_scores = [
            RequirementScoreResult(
                surface=r.surface,
                coverage_score=r.coverage_score,
                matched_count=r.matched_count,
                missing_count=r.missing_count,
                explanation=r.explanation,
            )
            for r in req_rows
        ]
        findings = [
            FindingResult(
                category=f.category,
                title=f.title,
                detail=f.detail,
                severity=f.severity,
                related_surface=f.related_surface,
                related_item=f.related_item,
                priority=f.priority,
            )
            for f in finding_rows
        ]
        by_cat: dict[str, list[FindingResult]] = {}
        for f in findings:
            by_cat.setdefault(f.category, []).append(f)

        plan = ArticlePlan.from_dict(json.loads(ev.article_plan_snapshot_json))
        return TwinEvaluationReport(
            twin_id=twin.id,
            evaluation_id=ev.id,
            evaluation_number=ev.evaluation_number,
            plan_revision=ev.plan_revision,
            client_brand=twin.client_brand,
            methodology=twin.methodology,
            article_plan=plan,
            predicted_strength_score=ev.predicted_strength_score,
            readiness_score=ev.readiness_score,
            summary=ev.summary,
            requirement_scores=requirement_scores,
            findings=findings,
            findings_by_category=by_cat,
        )
