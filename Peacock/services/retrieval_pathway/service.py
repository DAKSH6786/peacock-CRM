"""Retrieval Pathway Intelligence orchestration service."""

from __future__ import annotations

import json
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.retrieval_pathway import (
    METHODOLOGY_DISCLAIMER,
    RetrievalPathwayAnalysis,
    RpiBottleneckDiagnosis,
    RpiCauseClassification,
    RpiEvidence,
)
from retrieval_pathway.forensics import ObservedEvidenceInput, run_forensics
from retrieval_pathway.models import RetrievalPathwayReport, RetrievalPathwaySpec


def _domain(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = (parsed.netloc or parsed.path.split("/")[0]).lower()
    return host.removeprefix("www.")


class RetrievalPathwayService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: RetrievalPathwaySpec,
        created_by: str | None = None,
    ) -> RetrievalPathwayReport:
        if not spec.query_cluster.strip():
            raise ValueError("query_cluster is required")
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")
        if not spec.target_url.strip():
            raise ValueError("target_url is required")

        forensic = run_forensics(spec.evidence)
        domain = _domain(spec.target_url)

        analysis = RetrievalPathwayAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            query_cluster=spec.query_cluster.strip(),
            client_brand=spec.client_brand.strip(),
            target_url=spec.target_url.strip(),
            target_domain=domain,
            analysis_status="running",
            methodology="inferred_retrieval_pathway",
            proprietary_ranking_access_claimed=False,
            methodology_disclaimer=METHODOLOGY_DISCLAIMER,
            primary_bottleneck_stage=forensic.bottleneck.bottleneck_stage,
            primary_bottleneck_label=forensic.bottleneck.headline,
            estimated_retrieval_likelihood=forensic.estimated_retrieval_likelihood,
            estimated_selection_likelihood=forensic.estimated_selection_likelihood,
            retrieval_likelihood_band=forensic.retrieval_likelihood_band,
            selection_likelihood_band=forensic.selection_likelihood_band,
            overall_uncertainty=forensic.overall_uncertainty,
            interpretation=forensic.bottleneck.interpretation,
            recommended_investigation=forensic.bottleneck.recommended_investigation,
            observation_count=spec.evidence.observation_sample_size,
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        for item in forensic.evidence_summary:
            self.db.add(
                RpiEvidence(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    evidence_code=item["evidence_code"],
                    label=item["label"],
                    observed_value=item.get("observed_value"),
                    observed_text=item.get("observed_text"),
                    source=item.get("source") or "observed",
                    confidence=spec.evidence.evidence_confidence,
                )
            )

        for cause in forensic.causes:
            self.db.add(
                RpiCauseClassification(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    cause_code=cause.cause_code,
                    estimated_likelihood=cause.estimated_likelihood,
                    likelihood_band=cause.likelihood_band,
                    uncertainty=cause.uncertainty,
                    supporting_evidence=json.dumps(cause.supporting_evidence),
                    contrary_evidence=json.dumps(cause.contrary_evidence),
                    rationale=cause.rationale,
                    is_primary=cause.is_primary,
                )
            )

        self.db.add(
            RpiBottleneckDiagnosis(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                analysis_id=analysis.id,
                bottleneck_stage=forensic.bottleneck.bottleneck_stage,
                headline=forensic.bottleneck.headline,
                retrieval_probability_band=forensic.bottleneck.retrieval_probability_band,
                citation_selection_band=forensic.bottleneck.citation_selection_band,
                estimated_retrieval_likelihood=forensic.bottleneck.estimated_retrieval_likelihood,
                estimated_selection_likelihood=forensic.bottleneck.estimated_selection_likelihood,
                interpretation=forensic.bottleneck.interpretation,
                recommended_investigation=forensic.bottleneck.recommended_investigation,
                uncertainty=forensic.bottleneck.uncertainty,
                disclaimer=METHODOLOGY_DISCLAIMER,
            )
        )

        analysis.analysis_status = "ready"
        self.db.commit()

        return RetrievalPathwayReport(
            analysis_id=analysis.id,
            query_cluster=analysis.query_cluster,
            client_brand=analysis.client_brand,
            target_url=analysis.target_url,
            target_domain=domain,
            methodology=analysis.methodology,
            proprietary_ranking_access_claimed=False,
            disclaimer=METHODOLOGY_DISCLAIMER,
            forensic=forensic,
            example_display=self._example_display(forensic),
        )

    def get_report(
        self, *, analysis_id: str, organisation_id: str
    ) -> RetrievalPathwayReport | None:
        analysis = self.db.scalar(
            select(RetrievalPathwayAnalysis).where(
                RetrievalPathwayAnalysis.id == analysis_id,
                RetrievalPathwayAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        causes = list(
            self.db.scalars(
                select(RpiCauseClassification)
                .where(RpiCauseClassification.analysis_id == analysis_id)
                .order_by(RpiCauseClassification.estimated_likelihood.desc())
            ).all()
        )
        bottleneck_row = self.db.scalar(
            select(RpiBottleneckDiagnosis).where(
                RpiBottleneckDiagnosis.analysis_id == analysis_id
            )
        )
        from retrieval_pathway.forensics import (
            BottleneckResult,
            CauseResult,
            ForensicReport,
        )

        cause_results = [
            CauseResult(
                cause_code=c.cause_code,
                estimated_likelihood=c.estimated_likelihood,
                likelihood_band=c.likelihood_band,
                uncertainty=c.uncertainty,
                supporting_evidence=json.loads(c.supporting_evidence or "[]"),
                contrary_evidence=json.loads(c.contrary_evidence or "[]"),
                rationale=c.rationale,
                is_primary=c.is_primary,
            )
            for c in causes
        ]
        if bottleneck_row is None:
            return None
        bottleneck = BottleneckResult(
            bottleneck_stage=bottleneck_row.bottleneck_stage,
            headline=bottleneck_row.headline,
            retrieval_probability_band=bottleneck_row.retrieval_probability_band,
            citation_selection_band=bottleneck_row.citation_selection_band,
            estimated_retrieval_likelihood=bottleneck_row.estimated_retrieval_likelihood,
            estimated_selection_likelihood=bottleneck_row.estimated_selection_likelihood,
            interpretation=bottleneck_row.interpretation,
            recommended_investigation=bottleneck_row.recommended_investigation,
            uncertainty=bottleneck_row.uncertainty,
            disclaimer=bottleneck_row.disclaimer,
        )
        forensic = ForensicReport(
            estimated_retrieval_likelihood=analysis.estimated_retrieval_likelihood or 0.0,
            estimated_selection_likelihood=analysis.estimated_selection_likelihood or 0.0,
            retrieval_likelihood_band=analysis.retrieval_likelihood_band or "MEDIUM",
            selection_likelihood_band=analysis.selection_likelihood_band or "MEDIUM",
            causes=cause_results,
            bottleneck=bottleneck,
            overall_uncertainty=analysis.overall_uncertainty or "moderate",
        )
        return RetrievalPathwayReport(
            analysis_id=analysis.id,
            query_cluster=analysis.query_cluster,
            client_brand=analysis.client_brand,
            target_url=analysis.target_url,
            target_domain=analysis.target_domain,
            methodology=analysis.methodology,
            proprietary_ranking_access_claimed=False,
            disclaimer=METHODOLOGY_DISCLAIMER,
            forensic=forensic,
            example_display=self._example_display(forensic),
        )

    @staticmethod
    def _example_display(forensic) -> dict:
        b = forensic.bottleneck
        return {
            "headline": b.headline,
            "retrieval_probability": b.retrieval_probability_band,
            "citation_selection": b.citation_selection_band,
            "interpretation": b.interpretation,
            "recommended_investigation": b.recommended_investigation,
            "uncertainty": b.uncertainty,
            "disclaimer": METHODOLOGY_DISCLAIMER,
        }
