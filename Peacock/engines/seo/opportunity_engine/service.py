"""Peacock Opportunity Engine orchestration — always-on scans + adaptive ranking."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.opportunity_engine import (
    METHODOLOGY,
    OpportunityScan,
    PeacockOpportunity,
    PoEvidence,
    PoOutcomeFeedback,
    PoRankingFactor,
    PoRankingWeight,
)
from opportunity_engine.models import OpportunityScanReport, OpportunityScanSpec
from opportunity_engine.ranking import (
    EvidenceResult,
    OpportunityResult,
    OutcomeFeedbackInput,
    RankingFactorResult,
    ScanResult,
    WeightSnapshot,
    detect_and_rank,
    learn_weights_from_outcomes,
)


class OpportunityEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_scan(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: OpportunityScanSpec,
        created_by: str | None = None,
        persist_feedback: bool = True,
    ) -> OpportunityScanReport:
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")
        if not spec.signals:
            raise ValueError("At least one opportunity signal is required")

        # Load prior feedback for this website + any provided in-request
        prior = list(
            self.db.scalars(
                select(PoOutcomeFeedback).where(
                    PoOutcomeFeedback.organisation_id == organisation_id,
                    PoOutcomeFeedback.website_id == spec.website_id,
                )
            ).all()
        )
        feedback_inputs = [
            OutcomeFeedbackInput(
                opportunity_type=p.opportunity_type,
                impact=p.impact,
                urgency=p.urgency,
                confidence=p.confidence,
                difficulty=p.difficulty,
                expected_value=p.expected_value,
                predicted_score=p.predicted_score,
                realized_outcome=p.realized_outcome,
                opportunity_key=p.opportunity_key,
                outcome_label=p.outcome_label,
                notes=p.notes,
            )
            for p in prior
        ] + list(spec.outcome_feedback)

        model = learn_weights_from_outcomes(feedback_inputs)
        result = detect_and_rank(spec.signals, model=model)

        scan = OpportunityScan(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.client_brand.strip(),
            scan_status="completed",
            methodology=METHODOLOGY,
            always_on_layer=True,
            ranking_model_version=result.ranking_model_version,
            ranking_is_adaptive=True,
            fixed_formula_rejected=True,
            opportunity_count=len(result.opportunities),
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(scan)
        self.db.flush()

        for w in result.ranking_weights:
            self.db.add(
                PoRankingWeight(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=scan.id,
                    feature_code=w.feature_code,
                    base_weight=w.base_weight,
                    learned_weight=w.learned_weight,
                    effective_weight=w.effective_weight,
                    learning_sample_size=w.learning_sample_size,
                    explanation=w.explanation,
                )
            )

        for opp in result.opportunities:
            row = PeacockOpportunity(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                scan_id=scan.id,
                opportunity_key=opp.opportunity_key,
                opportunity_type=opp.opportunity_type,
                title=opp.title,
                description=opp.description,
                impact=opp.impact,
                urgency=opp.urgency,
                confidence=opp.confidence,
                difficulty=opp.difficulty,
                expected_value=opp.expected_value,
                recommended_action=opp.recommended_action,
                rank=opp.rank,
                opportunity_score=opp.opportunity_score,
                ranking_explanation=opp.ranking_explanation,
                related_entity=opp.related_entity,
                related_url=opp.related_url,
                status_label="open",
            )
            self.db.add(row)
            self.db.flush()
            for ev in opp.evidence:
                self.db.add(
                    PoEvidence(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        opportunity_id=row.id,
                        evidence_type=ev.evidence_type,
                        statement=ev.statement,
                        source_ref=ev.source_ref,
                        strength=ev.strength,
                    )
                )
            for f in opp.ranking_factors:
                self.db.add(
                    PoRankingFactor(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        opportunity_id=row.id,
                        feature_code=f.feature_code,
                        feature_value=f.feature_value,
                        weight=f.weight,
                        contribution=f.contribution,
                        weight_source=f.weight_source,
                        explanation=f.explanation,
                    )
                )

        if persist_feedback and spec.outcome_feedback:
            for fb in spec.outcome_feedback:
                self.db.add(
                    PoOutcomeFeedback(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        website_id=spec.website_id,
                        opportunity_type=fb.opportunity_type,
                        opportunity_key=fb.opportunity_key,
                        impact=fb.impact,
                        urgency=fb.urgency,
                        confidence=fb.confidence,
                        difficulty=fb.difficulty,
                        expected_value=fb.expected_value,
                        predicted_score=fb.predicted_score,
                        realized_outcome=fb.realized_outcome,
                        outcome_label=fb.outcome_label,
                        notes=fb.notes,
                    )
                )

        self.db.commit()
        return OpportunityScanReport(
            scan_id=scan.id,
            name=scan.name,
            client_brand=scan.client_brand,
            methodology=scan.methodology,
            always_on_layer=True,
            result=result,
        )

    def record_outcome(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        website_id: str,
        feedback: OutcomeFeedbackInput,
        created_by: str | None = None,
    ) -> dict:
        """Record realized outcome so future scans improve ranking."""
        row = PoOutcomeFeedback(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=website_id,
            opportunity_type=feedback.opportunity_type,
            opportunity_key=feedback.opportunity_key,
            impact=feedback.impact,
            urgency=feedback.urgency,
            confidence=feedback.confidence,
            difficulty=feedback.difficulty,
            expected_value=feedback.expected_value,
            predicted_score=feedback.predicted_score,
            realized_outcome=feedback.realized_outcome,
            outcome_label=feedback.outcome_label,
            notes=feedback.notes,
        )
        self.db.add(row)
        self.db.commit()
        return {
            "feedback_id": row.id,
            "opportunity_type": row.opportunity_type,
            "realized_outcome": row.realized_outcome,
            "note": "Outcome recorded; future scans will blend learned ranking weights.",
        }

    def get_scan(
        self, *, scan_id: str, organisation_id: str
    ) -> OpportunityScanReport | None:
        scan = self.db.scalar(
            select(OpportunityScan).where(
                OpportunityScan.id == scan_id,
                OpportunityScan.organisation_id == organisation_id,
            )
        )
        if scan is None:
            return None

        weight_rows = list(
            self.db.scalars(
                select(PoRankingWeight).where(PoRankingWeight.scan_id == scan.id)
            ).all()
        )
        ranking_weights = [
            WeightSnapshot(
                feature_code=w.feature_code,
                base_weight=w.base_weight,
                learned_weight=w.learned_weight,
                effective_weight=w.effective_weight,
                learning_sample_size=w.learning_sample_size,
                explanation=w.explanation,
            )
            for w in weight_rows
        ]

        opp_rows = list(
            self.db.scalars(
                select(PeacockOpportunity)
                .where(PeacockOpportunity.scan_id == scan.id)
                .order_by(PeacockOpportunity.rank.asc())
            ).all()
        )
        opportunities: list[OpportunityResult] = []
        for o in opp_rows:
            evidence = [
                EvidenceResult(
                    evidence_type=e.evidence_type,
                    statement=e.statement,
                    source_ref=e.source_ref,
                    strength=e.strength,
                )
                for e in self.db.scalars(
                    select(PoEvidence).where(PoEvidence.opportunity_id == o.id)
                ).all()
            ]
            factors = [
                RankingFactorResult(
                    feature_code=f.feature_code,
                    feature_value=f.feature_value,
                    weight=f.weight,
                    contribution=f.contribution,
                    weight_source=f.weight_source,
                    explanation=f.explanation,
                )
                for f in self.db.scalars(
                    select(PoRankingFactor).where(PoRankingFactor.opportunity_id == o.id)
                ).all()
            ]
            opportunities.append(
                OpportunityResult(
                    opportunity_key=o.opportunity_key,
                    opportunity_type=o.opportunity_type,
                    title=o.title,
                    description=o.description,
                    impact=o.impact,
                    urgency=o.urgency,
                    confidence=o.confidence,
                    difficulty=o.difficulty,
                    expected_value=o.expected_value,
                    recommended_action=o.recommended_action,
                    evidence=evidence,
                    rank=o.rank,
                    opportunity_score=o.opportunity_score,
                    ranking_explanation=o.ranking_explanation,
                    ranking_factors=factors,
                    related_entity=o.related_entity,
                    related_url=o.related_url,
                )
            )

        from db_models.opportunity_engine import ALWAYS_ON_NOTE, METHODOLOGY_NOTE

        result = ScanResult(
            opportunities=opportunities,
            ranking_weights=ranking_weights,
            ranking_model_version=scan.ranking_model_version,
            ranking_is_adaptive=scan.ranking_is_adaptive,
            fixed_formula_rejected=scan.fixed_formula_rejected,
            always_on_note=ALWAYS_ON_NOTE,
            methodology_note=METHODOLOGY_NOTE,
            summary=scan.summary or "",
        )
        return OpportunityScanReport(
            scan_id=scan.id,
            name=scan.name,
            client_brand=scan.client_brand,
            methodology=scan.methodology,
            always_on_layer=scan.always_on_layer,
            result=result,
        )
