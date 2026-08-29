"""Final Architecture service — persist Peacock One system maps."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.final_architecture import (
    ARCHITECTURE_POSITIONING,
    METHODOLOGY,
    PRODUCT_STANDARD,
    FaObservationSource,
    FaPineLane,
    FaPipelineStage,
    FaProductQuestion,
    FinalArchitectureMap,
)
from final_architecture.engine import (
    FinalArchitectureResult,
    ObservationSourceView,
    PineLaneView,
    PipelineStageView,
    ProductQuestionView,
    build_architecture_map,
)
from final_architecture.models import FinalArchitectureCreateSpec, FinalArchitectureReport


class FinalArchitectureService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_map(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: FinalArchitectureCreateSpec,
        created_by: str | None = None,
    ) -> FinalArchitectureReport:
        result = build_architecture_map(spec.architecture)

        row = FinalArchitectureMap(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            stages_count=result.stages_count,
            observation_sources_count=result.observation_sources_count,
            pine_lanes_count=result.pine_lanes_count,
            product_questions_count=result.product_questions_count,
            learning_loops_to_pine=result.learning_loops_to_pine,
            not_only_visibility=result.not_only_visibility,
            product_standard_coverage=result.product_standard_coverage,
            architecture_diagram=result.architecture_diagram,
            methodology=METHODOLOGY,
            architecture_positioning=ARCHITECTURE_POSITIONING,
            product_standard=PRODUCT_STANDARD,
            summary=result.summary,
            analysed_at=result.analysed_at,
            notes=spec.notes,
        )
        self.db.add(row)
        self.db.flush()

        for s in result.stages:
            self.db.add(
                FaPipelineStage(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    map_id=row.id,
                    stage_key=s.stage_key,
                    stage_label=s.stage_label,
                    rank_order=s.rank_order,
                    next_stage_key=s.next_stage_key,
                    loops_to_stage_key=s.loops_to_stage_key,
                    detail=s.detail,
                )
            )
        for o in result.observation_sources:
            self.db.add(
                FaObservationSource(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    map_id=row.id,
                    source_key=o.source_key,
                    source_label=o.source_label,
                    feeds_evidence_ledger=o.feeds_evidence_ledger,
                    rank_order=o.rank_order,
                )
            )
        for p in result.pine_lanes:
            self.db.add(
                FaPineLane(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    map_id=row.id,
                    lane_key=p.lane_key,
                    lane_label=p.lane_label,
                    rank_order=p.rank_order,
                    detail=p.detail,
                )
            )
        for q in result.product_questions:
            self.db.add(
                FaProductQuestion(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    map_id=row.id,
                    question_key=q.question_key,
                    question_text=q.question_text,
                    required=q.required,
                    addressed=q.addressed,
                    primary_stage_key=q.primary_stage_key,
                    rank_order=q.rank_order,
                )
            )

        self.db.commit()
        return FinalArchitectureReport(
            map_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )

    def get_map(
        self, *, map_id: str, organisation_id: str
    ) -> FinalArchitectureReport | None:
        row = self.db.scalar(
            select(FinalArchitectureMap).where(
                FinalArchitectureMap.id == map_id,
                FinalArchitectureMap.organisation_id == organisation_id,
            )
        )
        if row is None:
            return None

        stages = [
            PipelineStageView(
                stage_key=s.stage_key,
                stage_label=s.stage_label,
                rank_order=s.rank_order,
                next_stage_key=s.next_stage_key,
                loops_to_stage_key=s.loops_to_stage_key,
                detail=s.detail,
            )
            for s in self.db.scalars(
                select(FaPipelineStage)
                .where(FaPipelineStage.map_id == row.id)
                .order_by(FaPipelineStage.rank_order.asc())
            ).all()
        ]
        sources = [
            ObservationSourceView(
                source_key=o.source_key,
                source_label=o.source_label,
                feeds_evidence_ledger=o.feeds_evidence_ledger,
                rank_order=o.rank_order,
            )
            for o in self.db.scalars(
                select(FaObservationSource)
                .where(FaObservationSource.map_id == row.id)
                .order_by(FaObservationSource.rank_order.asc())
            ).all()
        ]
        lanes = [
            PineLaneView(
                lane_key=p.lane_key,
                lane_label=p.lane_label,
                rank_order=p.rank_order,
                detail=p.detail,
            )
            for p in self.db.scalars(
                select(FaPineLane)
                .where(FaPineLane.map_id == row.id)
                .order_by(FaPineLane.rank_order.asc())
            ).all()
        ]
        questions = [
            ProductQuestionView(
                question_key=q.question_key,
                question_text=q.question_text,
                required=q.required,
                addressed=q.addressed,
                primary_stage_key=q.primary_stage_key,
                rank_order=q.rank_order,
            )
            for q in self.db.scalars(
                select(FaProductQuestion)
                .where(FaProductQuestion.map_id == row.id)
                .order_by(FaProductQuestion.rank_order.asc())
            ).all()
        ]

        from db_models.final_architecture import METHODOLOGY_NOTE, NOT_ONLY_VISIBILITY

        result = FinalArchitectureResult(
            client_brand=row.client_brand,
            stages=stages,
            observation_sources=sources,
            pine_lanes=lanes,
            product_questions=questions,
            stages_count=row.stages_count,
            observation_sources_count=row.observation_sources_count,
            pine_lanes_count=row.pine_lanes_count,
            product_questions_count=row.product_questions_count,
            learning_loops_to_pine=row.learning_loops_to_pine,
            not_only_visibility=row.not_only_visibility,
            product_standard_coverage=row.product_standard_coverage,
            architecture_diagram=row.architecture_diagram,
            architecture_positioning=row.architecture_positioning,
            product_standard=row.product_standard,
            not_only_visibility_note=NOT_ONLY_VISIBILITY,
            methodology_note=METHODOLOGY_NOTE,
            summary=row.summary,
            analysed_at=row.analysed_at,
        )
        return FinalArchitectureReport(
            map_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )
