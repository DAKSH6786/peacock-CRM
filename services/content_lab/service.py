"""Peacock Content Lab orchestration service."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from content_lab.models import ContentLabReport, ContentLabSpec
from content_lab.scoring import (
    CitabilityComponentResult,
    InfoGainSignalResult,
    ProposalInput,
    ProposalScore,
    evaluate_proposals,
)
from db_models.base import new_uuid
from db_models.content_lab import (
    CITABILITY_DISCLAIMER,
    MOAT_FORMAT_PRIORS,
    ClCitabilityComponent,
    ClContentProposal,
    ClInfoGainSignal,
    ContentLabAnalysis,
)


class ContentLabService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: ContentLabSpec,
        created_by: str | None = None,
    ) -> ContentLabReport:
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")
        if not spec.proposals:
            raise ValueError("At least one content proposal is required")

        scores = evaluate_proposals(spec.proposals)

        analysis = ContentLabAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.client_brand.strip(),
            topic_cluster=spec.topic_cluster,
            analysis_status="running",
            methodology="content_lab_multi_opportunity",
            citability_is_proprietary_estimate=True,
            citability_disclaimer=CITABILITY_DISCLAIMER,
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        for score in scores:
            proposal = ClContentProposal(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                analysis_id=analysis.id,
                title=score.title,
                slug=score.slug,
                content_format=score.content_format,
                angle=score.angle,
                target_url=score.target_url,
                lab_priority_score=score.lab_priority_score,
                seo_opportunity=score.opportunities["seo_opportunity"],
                aeo_opportunity=score.opportunities["aeo_opportunity"],
                geo_opportunity=score.opportunities["geo_opportunity"],
                ai_citation_opportunity=score.opportunities["ai_citation_opportunity"],
                business_value=score.opportunities["business_value"],
                audience_relevance=score.opportunities["audience_relevance"],
                competitor_gap=score.opportunities["competitor_gap"],
                information_gain=score.opportunities["information_gain"],
                originality_opportunity=score.opportunities["originality_opportunity"],
                topical_authority_impact=score.opportunities["topical_authority_impact"],
                conversion_potential=score.opportunities["conversion_potential"],
                backlink_potential=score.opportunities["backlink_potential"],
                entity_impact=score.opportunities["entity_impact"],
                effort=score.opportunities["effort"],
                time_sensitivity=score.opportunities["time_sensitivity"],
                information_gain_score=score.information_gain_score,
                content_moat_score=score.content_moat_score,
                generative_citability_score=score.generative_citability_score,
                information_gain_breakdown=json.dumps(
                    [s.to_dict() for s in score.info_gain_signals]
                ),
                moat_rationale=score.moat_rationale,
                citability_breakdown=json.dumps(
                    [c.to_dict() for c in score.citability_components]
                ),
                recommendation_summary=score.recommendation_summary,
            )
            self.db.add(proposal)
            self.db.flush()

            for sig in score.info_gain_signals:
                self.db.add(
                    ClInfoGainSignal(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        proposal_id=proposal.id,
                        signal_code=sig.signal_code,
                        polarity=sig.polarity,
                        strength=sig.strength,
                        evidence=sig.evidence,
                    )
                )
            for comp in score.citability_components:
                self.db.add(
                    ClCitabilityComponent(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        proposal_id=proposal.id,
                        component_code=comp.component_code,
                        score=comp.score,
                        explanation=comp.explanation,
                    )
                )

        analysis.proposal_count = len(scores)
        analysis.analysis_status = "ready"
        self.db.commit()

        example_moat = [
            {"format": k.replace("_", " "), "moat_score": v}
            for k, v in MOAT_FORMAT_PRIORS.items()
        ]
        top = None
        if scores:
            s = scores[0]
            top = {
                "title": s.title,
                "lab_priority_score": s.lab_priority_score,
                "information_gain_score": s.information_gain_score,
                "content_moat_score": s.content_moat_score,
                "generative_citability_score": s.generative_citability_score,
                "summary": s.recommendation_summary,
            }

        return ContentLabReport(
            analysis_id=analysis.id,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            citability_is_proprietary_estimate=True,
            citability_disclaimer=CITABILITY_DISCLAIMER,
            proposals=scores,
            example_moat=example_moat,
            top_recommendation=top,
        )

    def get_report(
        self, *, analysis_id: str, organisation_id: str
    ) -> ContentLabReport | None:
        analysis = self.db.scalar(
            select(ContentLabAnalysis).where(
                ContentLabAnalysis.id == analysis_id,
                ContentLabAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        rows = list(
            self.db.scalars(
                select(ClContentProposal)
                .where(ClContentProposal.analysis_id == analysis_id)
                .order_by(ClContentProposal.lab_priority_score.desc())
            ).all()
        )
        scores: list[ProposalScore] = []
        for r in rows:
            ig = [
                InfoGainSignalResult(**x)
                for x in json.loads(r.information_gain_breakdown or "[]")
            ]
            cit = [
                CitabilityComponentResult(**x)
                for x in json.loads(r.citability_breakdown or "[]")
            ]
            scores.append(
                ProposalScore(
                    title=r.title,
                    slug=r.slug,
                    content_format=r.content_format,
                    angle=r.angle,
                    target_url=r.target_url,
                    lab_priority_score=r.lab_priority_score,
                    opportunities={
                        "seo_opportunity": r.seo_opportunity,
                        "aeo_opportunity": r.aeo_opportunity,
                        "geo_opportunity": r.geo_opportunity,
                        "ai_citation_opportunity": r.ai_citation_opportunity,
                        "business_value": r.business_value,
                        "audience_relevance": r.audience_relevance,
                        "competitor_gap": r.competitor_gap,
                        "information_gain": r.information_gain,
                        "originality_opportunity": r.originality_opportunity,
                        "topical_authority_impact": r.topical_authority_impact,
                        "conversion_potential": r.conversion_potential,
                        "backlink_potential": r.backlink_potential,
                        "entity_impact": r.entity_impact,
                        "effort": r.effort,
                        "time_sensitivity": r.time_sensitivity,
                    },
                    information_gain_score=r.information_gain_score,
                    content_moat_score=r.content_moat_score,
                    generative_citability_score=r.generative_citability_score,
                    info_gain_signals=ig,
                    citability_components=cit,
                    moat_rationale=r.moat_rationale or "",
                    recommendation_summary=r.recommendation_summary,
                )
            )

        example_moat = [
            {"format": k.replace("_", " "), "moat_score": v}
            for k, v in MOAT_FORMAT_PRIORS.items()
        ]
        top = None
        if scores:
            s = scores[0]
            top = {
                "title": s.title,
                "lab_priority_score": s.lab_priority_score,
                "information_gain_score": s.information_gain_score,
                "content_moat_score": s.content_moat_score,
                "generative_citability_score": s.generative_citability_score,
                "summary": s.recommendation_summary,
            }
        return ContentLabReport(
            analysis_id=analysis.id,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            citability_is_proprietary_estimate=True,
            citability_disclaimer=CITABILITY_DISCLAIMER,
            proposals=scores,
            example_moat=example_moat,
            top_recommendation=top,
        )
