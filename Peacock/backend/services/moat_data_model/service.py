"""Peacock Moat Data Model service — persist proprietary intelligence pathways."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.moat_data_model import (
    METHODOLOGY,
    MOAT_POSITIONING,
    MoatIntelligenceRun,
    MoatPathway,
    MoatPathwayEdge,
    MoatPathwayNode,
    MoatPathwayOutcome,
)
from moat_data_model.accumulation import (
    EdgeResult,
    MoatRunResult,
    NodeResult,
    OutcomeResult,
    PathwayResult,
    accumulate_moat,
)
from moat_data_model.models import MoatCreateSpec, MoatReport


class MoatDataModelService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def accumulate(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: MoatCreateSpec,
        created_by: str | None = None,
    ) -> MoatReport:
        result = accumulate_moat(spec.run)

        run = MoatIntelligenceRun(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            industry=result.industry,
            run_status="completed",
            methodology=METHODOLOGY,
            moat_positioning=MOAT_POSITIONING,
            pathways_count=result.pathways_count,
            nodes_count=result.nodes_count,
            edges_count=result.edges_count,
            outcomes_count=result.outcomes_count,
            moat_strength_score=result.moat_strength_score,
            mean_outcome_delta=result.mean_outcome_delta,
            mean_confidence=result.mean_confidence,
            summary=result.summary,
            analysed_at=result.analysed_at,
            notes=spec.notes,
        )
        self.db.add(run)
        self.db.flush()

        for p in result.pathways:
            pathway = MoatPathway(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                run_id=run.id,
                pathway_kind=p.pathway_kind,
                pathway_label=p.pathway_label,
                pathway_key=p.pathway_key,
                industry=p.industry,
                topic_key=p.topic_key,
                expected_score=p.expected_score,
                actual_score=p.actual_score,
                outcome_delta=p.outcome_delta,
                confidence=p.confidence,
                sample_weight=p.sample_weight,
                source_system=p.source_system,
                source_ref=p.source_ref,
                narrative=p.narrative,
                rank_order=p.rank_order,
            )
            self.db.add(pathway)
            self.db.flush()

            for n in p.nodes:
                self.db.add(
                    MoatPathwayNode(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        pathway_id=pathway.id,
                        node_ordinal=n.node_ordinal,
                        node_role=n.node_role,
                        node_kind=n.node_kind,
                        node_key=n.node_key,
                        label=n.label,
                    )
                )
            for e in p.edges:
                self.db.add(
                    MoatPathwayEdge(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        pathway_id=pathway.id,
                        from_ordinal=e.from_ordinal,
                        to_ordinal=e.to_ordinal,
                        edge_type=e.edge_type,
                        weight=e.weight,
                    )
                )
            for o in p.outcomes:
                self.db.add(
                    MoatPathwayOutcome(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        pathway_id=pathway.id,
                        metric_key=o.metric_key,
                        metric_value=o.metric_value,
                        baseline_value=o.baseline_value,
                        delta=o.delta,
                        observed_at=o.observed_at,
                        provenance=o.provenance,
                    )
                )

        self.db.commit()
        return MoatReport(
            run_id=run.id,
            name=run.name,
            client_brand=run.client_brand,
            methodology=run.methodology,
            result=result,
        )

    def get_run(
        self, *, run_id: str, organisation_id: str
    ) -> MoatReport | None:
        run = self.db.scalar(
            select(MoatIntelligenceRun).where(
                MoatIntelligenceRun.id == run_id,
                MoatIntelligenceRun.organisation_id == organisation_id,
            )
        )
        if run is None:
            return None

        pathways_orm = list(
            self.db.scalars(
                select(MoatPathway)
                .where(MoatPathway.run_id == run.id)
                .order_by(MoatPathway.rank_order.asc())
            ).all()
        )
        pathways: list[PathwayResult] = []
        for p in pathways_orm:
            nodes = [
                NodeResult(
                    node_ordinal=n.node_ordinal,
                    node_role=n.node_role,
                    node_kind=n.node_kind,
                    node_key=n.node_key,
                    label=n.label,
                )
                for n in self.db.scalars(
                    select(MoatPathwayNode)
                    .where(MoatPathwayNode.pathway_id == p.id)
                    .order_by(MoatPathwayNode.node_ordinal.asc())
                ).all()
            ]
            edges = [
                EdgeResult(
                    from_ordinal=e.from_ordinal,
                    to_ordinal=e.to_ordinal,
                    edge_type=e.edge_type,
                    weight=e.weight,
                )
                for e in self.db.scalars(
                    select(MoatPathwayEdge).where(MoatPathwayEdge.pathway_id == p.id)
                ).all()
            ]
            outcomes = [
                OutcomeResult(
                    metric_key=o.metric_key,
                    metric_value=o.metric_value,
                    baseline_value=o.baseline_value,
                    delta=o.delta,
                    observed_at=o.observed_at,
                    provenance=o.provenance,
                )
                for o in self.db.scalars(
                    select(MoatPathwayOutcome).where(
                        MoatPathwayOutcome.pathway_id == p.id
                    )
                ).all()
            ]
            pathways.append(
                PathwayResult(
                    pathway_kind=p.pathway_kind,
                    pathway_label=p.pathway_label,
                    pathway_key=p.pathway_key,
                    industry=p.industry,
                    topic_key=p.topic_key,
                    expected_score=p.expected_score,
                    actual_score=p.actual_score,
                    outcome_delta=p.outcome_delta,
                    confidence=p.confidence,
                    sample_weight=p.sample_weight,
                    source_system=p.source_system,
                    source_ref=p.source_ref,
                    narrative=p.narrative,
                    rank_order=p.rank_order,
                    nodes=nodes,
                    edges=edges,
                    outcomes=outcomes,
                )
            )

        from db_models.moat_data_model import METHODOLOGY_NOTE, NOT_UNIVERSAL_GEO

        result = MoatRunResult(
            client_brand=run.client_brand,
            industry=run.industry,
            pathways=pathways,
            pathways_count=run.pathways_count,
            nodes_count=run.nodes_count,
            edges_count=run.edges_count,
            outcomes_count=run.outcomes_count,
            moat_strength_score=run.moat_strength_score,
            mean_outcome_delta=run.mean_outcome_delta,
            mean_confidence=run.mean_confidence,
            pathway_kind_coverage=sorted({p.pathway_kind for p in pathways}),
            moat_positioning=run.moat_positioning,
            methodology_note=METHODOLOGY_NOTE,
            not_universal_geo=NOT_UNIVERSAL_GEO,
            summary=run.summary or "",
            analysed_at=run.analysed_at,
        )
        return MoatReport(
            run_id=run.id,
            name=run.name,
            client_brand=run.client_brand,
            methodology=run.methodology,
            result=result,
        )
