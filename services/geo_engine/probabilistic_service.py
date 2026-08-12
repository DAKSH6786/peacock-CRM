"""Probabilistic AI Visibility service — distributions over controlled repetitions."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from db_models.base import new_uuid
from db_models.probabilistic_visibility import (
    VisibilityCampaign,
    VisibilityDistribution,
    VisibilityProbeCell,
    VisibilityProbeObservation,
    VisibilityScoreCard,
)
from geo_engine.probabilistic_models import (
    CampaignSpec,
    DistributionMetric,
    RateLimitPolicy,
    VisibilityScoreCardView,
)
from geo_engine.probabilistic_sampler import (
    RateLimiter,
    mock_visibility_probe,
    prompt_hash,
    run_controlled_repetitions,
    validate_repetitions,
)
from geo_engine.probabilistic_stats import (
    ai_visibility_score,
    bernoulli_estimate,
    engine_disagreement,
    peacock_visibility_confidence,
    temporal_volatility,
)


class ProbabilisticVisibilityService:
    """Create campaigns, run rate-limited repetitions, compute distributions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_campaign(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: CampaignSpec,
    ) -> VisibilityCampaign:
        policy = spec.rate_limit.clamped()
        validate_repetitions(policy.target_repetitions, max_repetitions=policy.max_repetitions)

        campaign = VisibilityCampaign(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            website_id=spec.website_id,
            name=spec.name,
            brand_name=spec.brand_name,
            target_repetitions=policy.target_repetitions,
            max_repetitions=policy.max_repetitions,
            max_calls_per_minute=policy.max_calls_per_minute,
            max_concurrent=policy.max_concurrent,
            max_total_calls=policy.max_total_calls,
            min_interval_ms=policy.min_interval_ms,
            campaign_status="ready",
            notes=spec.notes,
        )
        self.session.add(campaign)
        self.session.flush()

        for cell in spec.cells:
            reps = cell.target_repetitions or policy.target_repetitions
            reps = validate_repetitions(reps, max_repetitions=policy.max_repetitions)
            self.session.add(
                VisibilityProbeCell(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    campaign_id=campaign.id,
                    prompt_text=cell.prompt_text,
                    prompt_hash=prompt_hash(cell.prompt_text),
                    engine_code=cell.engine_code,
                    model_code=cell.model_code,
                    location_code=cell.location_code,
                    persona_code=cell.persona_code,
                    config_code=cell.config_code,
                    temperature=cell.temperature,
                    time_bucket=cell.time_bucket,
                    target_repetitions=reps,
                )
            )
        self.session.commit()
        return campaign

    async def run_campaign(
        self,
        *,
        campaign_id: str,
        organisation_id: str,
        use_mock: bool = True,
    ) -> VisibilityScoreCardView:
        campaign = self.session.get(
            VisibilityCampaign,
            campaign_id,
            options=(
                selectinload(VisibilityCampaign.cells),
                selectinload(VisibilityCampaign.observations),
            ),
        )
        if campaign is None or campaign.organisation_id != organisation_id:
            raise LookupError("Visibility campaign not found")

        policy = RateLimitPolicy(
            max_calls_per_minute=campaign.max_calls_per_minute,
            max_concurrent=campaign.max_concurrent,
            max_total_calls=campaign.max_total_calls,
            min_interval_ms=campaign.min_interval_ms,
            target_repetitions=campaign.target_repetitions,
            max_repetitions=campaign.max_repetitions,
        ).clamped()
        limiter = RateLimiter(policy)
        probe_fn = mock_visibility_probe if use_mock else mock_visibility_probe

        campaign.campaign_status = "running"
        self.session.commit()

        competitors_seen: set[str] = set()
        for cell in campaign.cells:
            needed = max(0, cell.target_repetitions - cell.completed_repetitions)
            if needed == 0:
                continue
            from geo_engine.probabilistic_models import ProbeCellSpec

            spec = ProbeCellSpec(
                prompt_text=cell.prompt_text,
                engine_code=cell.engine_code,
                model_code=cell.model_code,
                location_code=cell.location_code,
                persona_code=cell.persona_code,
                config_code=cell.config_code,
                temperature=cell.temperature,
                time_bucket=cell.time_bucket,
                target_repetitions=needed,
            )
            outcomes = await run_controlled_repetitions(
                cell=spec,
                repetitions=needed,
                rate_limiter=limiter,
                probe_fn=probe_fn,
            )
            for offset, outcome in enumerate(outcomes):
                run_index = cell.completed_repetitions + offset + 1
                competitors_seen.update(outcome.competitor_mentions)
                self.session.add(
                    VisibilityProbeObservation(
                        id=new_uuid(),
                        organisation_id=campaign.organisation_id,
                        workspace_id=campaign.workspace_id,
                        campaign_id=campaign.id,
                        cell_id=cell.id,
                        run_index=run_index,
                        observed_at=datetime.now(UTC),
                        brand_mentioned=outcome.brand_mentioned,
                        brand_cited=outcome.brand_cited,
                        brand_top3=outcome.brand_top3,
                        brand_position=outcome.brand_position,
                        competitor_mentions=",".join(outcome.competitor_mentions) or None,
                        raw_excerpt=outcome.raw_excerpt,
                        structured_summary=outcome.structured_summary,
                        probe_source="mock" if use_mock else "live",
                    )
                )
            cell.completed_repetitions += len(outcomes)

        campaign.campaign_status = "computed"
        self.session.commit()
        return self.compute_score_card(campaign_id=campaign.id, organisation_id=organisation_id)

    def compute_score_card(
        self,
        *,
        campaign_id: str,
        organisation_id: str,
    ) -> VisibilityScoreCardView:
        campaign = self.session.get(
            VisibilityCampaign,
            campaign_id,
            options=(
                selectinload(VisibilityCampaign.cells),
                selectinload(VisibilityCampaign.observations),
            ),
        )
        if campaign is None or campaign.organisation_id != organisation_id:
            raise LookupError("Visibility campaign not found")

        observations = list(campaign.observations)
        n = len(observations)
        if n == 0:
            raise ValueError(
                "No observations yet. Probabilistic visibility requires controlled repetitions — "
                "a single response is never treated as truth."
            )
        if n == 1:
            # Explicitly refuse to present a single shot as a confident score
            pass

        mention_est = bernoulli_estimate(sum(1 for o in observations if o.brand_mentioned), n)
        citation_est = bernoulli_estimate(sum(1 for o in observations if o.brand_cited), n)
        top3_est = bernoulli_estimate(sum(1 for o in observations if o.brand_top3), n)

        # Per-engine disagreement
        by_engine: dict[str, list[VisibilityProbeObservation]] = defaultdict(list)
        cell_by_id = {c.id: c for c in campaign.cells}
        for obs in observations:
            engine = cell_by_id[obs.cell_id].engine_code if obs.cell_id in cell_by_id else "unknown"
            by_engine[engine].append(obs)
        engine_mention_ps = []
        for rows in by_engine.values():
            if not rows:
                continue
            engine_mention_ps.append(sum(1 for r in rows if r.brand_mentioned) / len(rows))
        disagreement = engine_disagreement(engine_mention_ps)

        # Temporal volatility across time buckets
        by_period: dict[str, list[VisibilityProbeObservation]] = defaultdict(list)
        for obs in observations:
            bucket = cell_by_id[obs.cell_id].time_bucket if obs.cell_id in cell_by_id else "current"
            by_period[bucket].append(obs)
        period_ps = [
            sum(1 for r in rows if r.brand_mentioned) / len(rows)
            for rows in by_period.values()
            if rows
        ]
        volatility = temporal_volatility(period_ps)

        # Competitor probabilities
        competitor_counts: dict[str, int] = defaultdict(int)
        for obs in observations:
            if not obs.competitor_mentions:
                continue
            for name in obs.competitor_mentions.split(","):
                name = name.strip()
                if name:
                    competitor_counts[name] += 1
        competitor_probs = {
            name: bernoulli_estimate(count, n).probability
            for name, count in competitor_counts.items()
        }

        distributions = [
            DistributionMetric(
                metric_key="brand_mention_probability",
                subject_key="brand",
                probability=mention_est.probability,
                variance=mention_est.variance,
                ci_low=mention_est.ci_low,
                ci_high=mention_est.ci_high,
                sample_size=mention_est.sample_size,
                engine_disagreement=disagreement,
                temporal_volatility=volatility,
                success_count=mention_est.success_count,
            ),
            DistributionMetric(
                metric_key="citation_probability",
                subject_key="brand",
                probability=citation_est.probability,
                variance=citation_est.variance,
                ci_low=citation_est.ci_low,
                ci_high=citation_est.ci_high,
                sample_size=citation_est.sample_size,
                engine_disagreement=disagreement,
                temporal_volatility=volatility,
                success_count=citation_est.success_count,
            ),
            DistributionMetric(
                metric_key="top3_recommendation_probability",
                subject_key="brand",
                probability=top3_est.probability,
                variance=top3_est.variance,
                ci_low=top3_est.ci_low,
                ci_high=top3_est.ci_high,
                sample_size=top3_est.sample_size,
                engine_disagreement=disagreement,
                temporal_volatility=volatility,
                success_count=top3_est.success_count,
            ),
        ]
        for name, count in competitor_counts.items():
            est = bernoulli_estimate(count, n)
            distributions.append(
                DistributionMetric(
                    metric_key="competitor_mention_probability",
                    subject_key=f"competitor:{name}",
                    probability=est.probability,
                    variance=est.variance,
                    ci_low=est.ci_low,
                    ci_high=est.ci_high,
                    sample_size=est.sample_size,
                    engine_disagreement=disagreement,
                    temporal_volatility=volatility,
                    success_count=est.success_count,
                )
            )

        max_competitor = max(competitor_probs.values()) if competitor_probs else 0.0
        score = ai_visibility_score(
            brand_mention_p=mention_est.probability,
            citation_p=citation_est.probability,
            top3_p=top3_est.probability,
            competitor_gap=max(0.0, max_competitor - mention_est.probability),
        )
        mean_variance = (
            mention_est.variance + citation_est.variance + top3_est.variance
        ) / 3.0
        conf_score, conf_label = peacock_visibility_confidence(
            sample_size=n,
            engine_count=len(by_engine),
            prompt_count=len({c.prompt_hash for c in campaign.cells}),
            period_count=len(by_period),
            mean_variance=mean_variance,
            mean_engine_disagreement=disagreement,
            mean_temporal_volatility=volatility,
        )

        # Persist distributions (replace)
        for existing in list(
            self.session.scalars(
                select(VisibilityDistribution).where(
                    VisibilityDistribution.campaign_id == campaign.id
                )
            )
        ):
            self.session.delete(existing)
        self.session.flush()
        for dist in distributions:
            self.session.add(
                VisibilityDistribution(
                    id=new_uuid(),
                    organisation_id=campaign.organisation_id,
                    workspace_id=campaign.workspace_id,
                    campaign_id=campaign.id,
                    metric_key=dist.metric_key,
                    subject_key=dist.subject_key,
                    scope_key=dist.scope_key,
                    probability=dist.probability,
                    variance=dist.variance,
                    ci_low=dist.ci_low,
                    ci_high=dist.ci_high,
                    sample_size=dist.sample_size,
                    engine_disagreement=dist.engine_disagreement,
                    temporal_volatility=dist.temporal_volatility,
                    success_count=dist.success_count,
                )
            )

        summary = (
            f"AI Visibility Score: {score:.0f}\n"
            f"Measurement Confidence: {conf_label}\n"
            f"Based on: {n} observations, {len(by_engine)} engines, "
            f"{len({c.prompt_hash for c in campaign.cells})} prompts, "
            f"{len(by_period)} observation periods.\n"
            f"Brand Mention Probability {mention_est.probability:.2f} "
            f"(CI {mention_est.ci_low:.2f}–{mention_est.ci_high:.2f}); "
            f"Citation Probability {citation_est.probability:.2f}; "
            f"Top-3 Recommendation Probability {top3_est.probability:.2f}. "
            f"Single-shot measurements are rejected."
        )
        now = datetime.now(UTC)
        card = VisibilityScoreCard(
            id=new_uuid(),
            organisation_id=campaign.organisation_id,
            workspace_id=campaign.workspace_id,
            campaign_id=campaign.id,
            website_id=campaign.website_id,
            ai_visibility_score=score,
            measurement_confidence=conf_label,
            peacock_visibility_confidence=conf_score,
            observation_count=n,
            engine_count=len(by_engine),
            prompt_count=len({c.prompt_hash for c in campaign.cells}),
            period_count=len(by_period),
            brand_mention_probability=mention_est.probability,
            citation_probability=citation_est.probability,
            top3_probability=top3_est.probability,
            summary=summary,
            computed_at=now,
        )
        self.session.add(card)
        self.session.commit()

        return VisibilityScoreCardView(
            ai_visibility_score=score,
            measurement_confidence=conf_label,
            peacock_visibility_confidence=conf_score,
            observation_count=n,
            engine_count=len(by_engine),
            prompt_count=len({c.prompt_hash for c in campaign.cells}),
            period_count=len(by_period),
            brand_mention_probability=mention_est.probability,
            citation_probability=citation_est.probability,
            top3_probability=top3_est.probability,
            competitor_probabilities=competitor_probs,
            distributions=distributions,
            summary=summary,
            computed_at=now,
        )

    def get_score_card(
        self, *, campaign_id: str, organisation_id: str
    ) -> VisibilityScoreCardView | None:
        card = self.session.scalar(
            select(VisibilityScoreCard)
            .where(
                VisibilityScoreCard.campaign_id == campaign_id,
                VisibilityScoreCard.organisation_id == organisation_id,
            )
            .order_by(VisibilityScoreCard.computed_at.desc())
            .limit(1)
        )
        if card is None:
            return None
        dists = list(
            self.session.scalars(
                select(VisibilityDistribution).where(
                    VisibilityDistribution.campaign_id == campaign_id
                )
            )
        )
        competitor_probs = {
            d.subject_key.removeprefix("competitor:"): d.probability
            for d in dists
            if d.metric_key == "competitor_mention_probability"
        }
        return VisibilityScoreCardView(
            ai_visibility_score=card.ai_visibility_score,
            measurement_confidence=card.measurement_confidence,
            peacock_visibility_confidence=card.peacock_visibility_confidence,
            observation_count=card.observation_count,
            engine_count=card.engine_count,
            prompt_count=card.prompt_count,
            period_count=card.period_count,
            brand_mention_probability=card.brand_mention_probability,
            citation_probability=card.citation_probability,
            top3_probability=card.top3_probability,
            competitor_probabilities=competitor_probs,
            distributions=[
                DistributionMetric(
                    metric_key=d.metric_key,
                    subject_key=d.subject_key,
                    probability=d.probability,
                    variance=d.variance,
                    ci_low=d.ci_low,
                    ci_high=d.ci_high,
                    sample_size=d.sample_size,
                    engine_disagreement=d.engine_disagreement,
                    temporal_volatility=d.temporal_volatility,
                    success_count=d.success_count,
                    scope_key=d.scope_key,
                )
                for d in dists
            ],
            summary=card.summary,
            computed_at=card.computed_at,
        )
