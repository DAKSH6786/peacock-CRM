"""Share of Answer orchestration service."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.share_of_answer import (
    ShareOfAnswerAnalysis,
    SoaAnswerObservation,
    SoaBrandScore,
    SoaEntityIndicator,
)
from share_of_answer.extractor import AnswerDocument, extract_entity_indicators
from share_of_answer.models import ShareOfAnswerReport, ShareOfAnswerSpec
from share_of_answer.scoring import (
    DEFAULT_INDICATOR_WEIGHTS,
    EntityIndicatorReading,
    aggregate_brand_scores,
    compute_influence,
)


class ShareOfAnswerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: ShareOfAnswerSpec,
        created_by: str | None = None,
    ) -> ShareOfAnswerReport:
        if not spec.observations:
            raise ValueError("At least one generative answer observation is required")
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")
        if not spec.query_cluster.strip():
            raise ValueError("query_cluster is required")

        weights = spec.indicator_weights or DEFAULT_INDICATOR_WEIGHTS
        # Reject token-only weight maps
        if set(weights.keys()) <= {"token_span", "token_span_ratio", "tokens"}:
            raise ValueError(
                "Token count alone is rejected as Share of Answer methodology; "
                "provide multiple indicators"
            )

        analysis = ShareOfAnswerAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            query_cluster=spec.query_cluster.strip(),
            client_brand=spec.client_brand.strip(),
            analysis_status="running",
            methodology="multi_indicator",
            token_count_alone_rejected=True,
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        all_readings: list[list[EntityIndicatorReading]] = []

        for obs_spec in spec.observations:
            document = AnswerDocument(
                prompt_text=obs_spec.prompt_text,
                engine_code=obs_spec.engine_code,
                raw_excerpt=obs_spec.raw_excerpt,
                model_code=obs_spec.model_code,
                answer_token_count=obs_spec.answer_token_count,
            )
            readings = extract_entity_indicators(
                document,
                client_brand=spec.client_brand,
                competitor_brands=spec.competitor_brands,
            )
            all_readings.append(readings)

            obs = SoaAnswerObservation(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                analysis_id=analysis.id,
                prompt_text=obs_spec.prompt_text,
                engine_code=obs_spec.engine_code,
                model_code=obs_spec.model_code,
                observed_at=datetime.now(UTC),
                raw_excerpt=obs_spec.raw_excerpt,
                structured_summary=self._summary(readings),
                answer_token_count=obs_spec.answer_token_count
                or len(obs_spec.raw_excerpt.split()),
                probe_source="mock",
            )
            self.db.add(obs)
            self.db.flush()

            for reading in readings:
                breakdown = compute_influence(reading, weights=weights)
                self.db.add(
                    SoaEntityIndicator(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        observation_id=obs.id,
                        entity_name=reading.entity_name,
                        is_client=reading.is_client,
                        mention=reading.mention,
                        mention_count=reading.mention_count,
                        position=reading.position,
                        recommendation_strength=reading.recommendation_strength,
                        answer_space=reading.answer_space,
                        citation_ownership=reading.citation_ownership,
                        semantic_prominence=reading.semantic_prominence,
                        positive_claims=reading.positive_claims,
                        negative_claims=reading.negative_claims,
                        neutral_claims=reading.neutral_claims,
                        comparison_outcome=reading.comparison_outcome,
                        token_span_ratio=reading.token_span_ratio,
                        influence_score=breakdown.influence,
                    )
                )

        aggregates = aggregate_brand_scores(
            entity_readings_per_observation=all_readings,
            weights=weights,
        )

        for agg in aggregates:
            self.db.add(
                SoaBrandScore(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    entity_name=agg.entity_name,
                    is_client=agg.is_client,
                    share_of_answer=agg.share_of_answer,
                    mention_rate=agg.mention_rate,
                    avg_position_score=agg.avg_position_score,
                    avg_recommendation_strength=agg.avg_recommendation_strength,
                    avg_answer_space=agg.avg_answer_space,
                    avg_citation_ownership=agg.avg_citation_ownership,
                    avg_semantic_prominence=agg.avg_semantic_prominence,
                    avg_claim_balance=agg.avg_claim_balance,
                    avg_comparison_score=agg.avg_comparison_score,
                    avg_token_span_ratio=agg.avg_token_span_ratio,
                    token_only_share=agg.token_only_share,
                    token_vs_influence_gap=agg.token_vs_influence_gap,
                    positive_claims_total=agg.positive_claims_total,
                    negative_claims_total=agg.negative_claims_total,
                    neutral_claims_total=agg.neutral_claims_total,
                    observation_sample_size=agg.observation_sample_size,
                    mean_influence=agg.mean_influence,
                )
            )

        analysis.observation_count = len(spec.observations)
        analysis.entity_count = len(aggregates)
        analysis.analysis_status = "ready"
        self.db.commit()

        return ShareOfAnswerReport(
            analysis_id=analysis.id,
            query_cluster=analysis.query_cluster,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            token_count_alone_rejected=True,
            observation_count=analysis.observation_count,
            brands=aggregates,
            indicator_weights=dict(weights),
        )

    def get_report(
        self, *, analysis_id: str, organisation_id: str
    ) -> ShareOfAnswerReport | None:
        analysis = self.db.scalar(
            select(ShareOfAnswerAnalysis).where(
                ShareOfAnswerAnalysis.id == analysis_id,
                ShareOfAnswerAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        scores = list(
            self.db.scalars(
                select(SoaBrandScore)
                .where(SoaBrandScore.analysis_id == analysis_id)
                .order_by(SoaBrandScore.share_of_answer.desc())
            ).all()
        )
        from share_of_answer.scoring import BrandAggregate

        brands = [
            BrandAggregate(
                entity_name=s.entity_name,
                is_client=s.is_client,
                share_of_answer=s.share_of_answer,
                mention_rate=s.mention_rate,
                avg_position_score=s.avg_position_score,
                avg_recommendation_strength=s.avg_recommendation_strength,
                avg_answer_space=s.avg_answer_space,
                avg_citation_ownership=s.avg_citation_ownership,
                avg_semantic_prominence=s.avg_semantic_prominence,
                avg_claim_balance=s.avg_claim_balance,
                avg_comparison_score=s.avg_comparison_score,
                avg_token_span_ratio=s.avg_token_span_ratio,
                token_only_share=s.token_only_share,
                token_vs_influence_gap=s.token_vs_influence_gap,
                positive_claims_total=s.positive_claims_total,
                negative_claims_total=s.negative_claims_total,
                neutral_claims_total=s.neutral_claims_total,
                observation_sample_size=s.observation_sample_size,
                mean_influence=s.mean_influence,
            )
            for s in scores
        ]
        return ShareOfAnswerReport(
            analysis_id=analysis.id,
            query_cluster=analysis.query_cluster,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            token_count_alone_rejected=analysis.token_count_alone_rejected,
            observation_count=analysis.observation_count,
            brands=brands,
            indicator_weights=dict(DEFAULT_INDICATOR_WEIGHTS),
        )

    @staticmethod
    def _summary(readings: list[EntityIndicatorReading]) -> str:
        mentioned = [r.entity_name for r in readings if r.mention]
        return f"entities_mentioned={','.join(mentioned) or 'none'}"
