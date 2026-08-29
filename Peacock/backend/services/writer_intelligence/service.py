"""Writer Intelligence 2.0 orchestration service."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.writer_intelligence import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    SIMILARITY_ONLY_REJECTED,
    WiDnaTrait,
    WiOutcomeEdge,
    WiOutcomeNode,
    WiPerformanceRecord,
    WiRecommendation,
    WiWriterDna,
    WriterIntelligenceAnalysis,
)
from writer_intelligence.models import WriterIntelligenceReport, WriterIntelligenceSpec
from writer_intelligence.scoring import (
    DnaTraitResult,
    IntelligenceResult,
    OutcomeEdge,
    OutcomeNode,
    PerformanceRecordResult,
    WriterDnaProfile,
    WriterRecommendationResult,
    recommend_writers,
)


class WriterIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: WriterIntelligenceSpec,
        created_by: str | None = None,
    ) -> WriterIntelligenceReport:
        result = recommend_writers(
            context=spec.context,
            writers=spec.writers,
            history=spec.history,
        )

        analysis = WriterIntelligenceAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.context.client_brand.strip(),
            industry=spec.context.industry.strip(),
            topic=spec.context.topic.strip(),
            audience=spec.context.audience.strip(),
            analysis_status="completed",
            methodology=METHODOLOGY,
            similarity_only_rejected=True,
            similarity_rejection_note=SIMILARITY_ONLY_REJECTED,
            decision_question=result.decision_question,
            top_writer_key=result.top_writer_key,
            top_outcome_score=result.top_outcome_score,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        for dna in result.dna_profiles:
            dna_row = WiWriterDna(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                analysis_id=analysis.id,
                writer_key=dna.writer_key,
                display_name=dna.display_name,
                dna_composite_score=dna.dna_composite_score,
                dna_summary=dna.dna_summary,
            )
            self.db.add(dna_row)
            self.db.flush()
            for trait in dna.traits:
                self.db.add(
                    WiDnaTrait(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        dna_id=dna_row.id,
                        trait_code=trait.trait_code,
                        score=trait.score,
                        evidence=trait.evidence,
                    )
                )

        for rec in result.recommendations:
            self.db.add(
                WiRecommendation(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    writer_key=rec.writer_key,
                    display_name=rec.display_name,
                    rank=rec.rank,
                    predicted_outcome_score=rec.predicted_outcome_score,
                    dna_fit_score=rec.dna_fit_score,
                    topic_fit_score=rec.topic_fit_score,
                    client_fit_score=rec.client_fit_score,
                    audience_fit_score=rec.audience_fit_score,
                    historical_outcome_score=rec.historical_outcome_score,
                    similarity_score_unused=rec.similarity_score_unused,
                    similarity_not_used_as_primary=True,
                    rationale=rec.rationale,
                    decision_answer=rec.decision_answer,
                )
            )

        for node in result.outcome_nodes:
            self.db.add(
                WiOutcomeNode(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    node_kind=node.node_kind,
                    node_key=node.node_key[:255],
                    label=node.label[:512],
                    attributes_json=json.dumps(node.attributes) if node.attributes else None,
                )
            )

        for edge in result.outcome_edges:
            self.db.add(
                WiOutcomeEdge(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    edge_type=edge.edge_type,
                    from_node_kind=edge.from_node_kind,
                    from_node_key=edge.from_node_key[:255],
                    to_node_kind=edge.to_node_kind,
                    to_node_key=edge.to_node_key[:255],
                    weight=edge.weight,
                )
            )

        for perf in result.performance_records:
            m = perf.metrics
            self.db.add(
                WiPerformanceRecord(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    article_key=perf.article_key,
                    writer_key=perf.writer_key,
                    client_key=perf.client_key,
                    industry=perf.industry,
                    topic=perf.topic,
                    approval=m.get("approval"),
                    revision_rounds=m.get("revision_rounds"),
                    ranking=m.get("ranking"),
                    impressions=m.get("impressions"),
                    ai_citations=m.get("ai_citations"),
                    engagement=m.get("engagement"),
                    links_earned=m.get("links_earned"),
                    conversion=m.get("conversion"),
                    composite_outcome=perf.composite_outcome,
                )
            )

        self.db.commit()
        return WriterIntelligenceReport(
            analysis_id=analysis.id,
            name=analysis.name,
            client_brand=analysis.client_brand,
            industry=analysis.industry,
            topic=analysis.topic,
            audience=analysis.audience,
            methodology=analysis.methodology,
            result=result,
        )

    def get_report(
        self, *, analysis_id: str, organisation_id: str
    ) -> WriterIntelligenceReport | None:
        analysis = self.db.scalar(
            select(WriterIntelligenceAnalysis).where(
                WriterIntelligenceAnalysis.id == analysis_id,
                WriterIntelligenceAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        dna_rows = list(
            self.db.scalars(
                select(WiWriterDna).where(WiWriterDna.analysis_id == analysis.id)
            ).all()
        )
        dna_profiles: list[WriterDnaProfile] = []
        for d in dna_rows:
            traits = list(
                self.db.scalars(
                    select(WiDnaTrait).where(WiDnaTrait.dna_id == d.id)
                ).all()
            )
            dna_profiles.append(
                WriterDnaProfile(
                    writer_key=d.writer_key,
                    display_name=d.display_name,
                    traits=[
                        DnaTraitResult(
                            trait_code=t.trait_code, score=t.score, evidence=t.evidence
                        )
                        for t in traits
                    ],
                    dna_composite_score=d.dna_composite_score,
                    dna_summary=d.dna_summary,
                )
            )

        recs = list(
            self.db.scalars(
                select(WiRecommendation)
                .where(WiRecommendation.analysis_id == analysis.id)
                .order_by(WiRecommendation.rank.asc())
            ).all()
        )
        recommendations = [
            WriterRecommendationResult(
                writer_key=r.writer_key,
                display_name=r.display_name,
                rank=r.rank,
                predicted_outcome_score=r.predicted_outcome_score,
                dna_fit_score=r.dna_fit_score,
                topic_fit_score=r.topic_fit_score,
                client_fit_score=r.client_fit_score,
                audience_fit_score=r.audience_fit_score,
                historical_outcome_score=r.historical_outcome_score,
                similarity_score_unused=r.similarity_score_unused,
                similarity_not_used_as_primary=r.similarity_not_used_as_primary,
                rationale=r.rationale,
                decision_answer=r.decision_answer,
            )
            for r in recs
        ]

        nodes = [
            OutcomeNode(
                node_kind=n.node_kind,
                node_key=n.node_key,
                label=n.label,
                attributes=json.loads(n.attributes_json) if n.attributes_json else {},
            )
            for n in self.db.scalars(
                select(WiOutcomeNode).where(WiOutcomeNode.analysis_id == analysis.id)
            ).all()
        ]
        edges = [
            OutcomeEdge(
                edge_type=e.edge_type,
                from_node_kind=e.from_node_kind,
                from_node_key=e.from_node_key,
                to_node_kind=e.to_node_kind,
                to_node_key=e.to_node_key,
                weight=e.weight,
            )
            for e in self.db.scalars(
                select(WiOutcomeEdge).where(WiOutcomeEdge.analysis_id == analysis.id)
            ).all()
        ]
        perf = [
            PerformanceRecordResult(
                article_key=p.article_key,
                writer_key=p.writer_key,
                client_key=p.client_key,
                industry=p.industry,
                topic=p.topic,
                metrics={
                    "approval": p.approval,
                    "revision_rounds": p.revision_rounds,
                    "ranking": p.ranking,
                    "impressions": p.impressions,
                    "ai_citations": p.ai_citations,
                    "engagement": p.engagement,
                    "links_earned": p.links_earned,
                    "conversion": p.conversion,
                },
                composite_outcome=p.composite_outcome,
            )
            for p in self.db.scalars(
                select(WiPerformanceRecord).where(
                    WiPerformanceRecord.analysis_id == analysis.id
                )
            ).all()
        ]

        result = IntelligenceResult(
            decision_question=analysis.decision_question,
            methodology_note=METHODOLOGY_NOTE,
            similarity_only_rejected=analysis.similarity_only_rejected,
            similarity_rejection_note=analysis.similarity_rejection_note,
            dna_profiles=dna_profiles,
            recommendations=recommendations,
            outcome_nodes=nodes,
            outcome_edges=edges,
            performance_records=perf,
            top_writer_key=analysis.top_writer_key,
            top_outcome_score=analysis.top_outcome_score,
            summary=analysis.summary or "",
        )

        return WriterIntelligenceReport(
            analysis_id=analysis.id,
            name=analysis.name,
            client_brand=analysis.client_brand,
            industry=analysis.industry,
            topic=analysis.topic,
            audience=analysis.audience,
            methodology=analysis.methodology,
            result=result,
        )
