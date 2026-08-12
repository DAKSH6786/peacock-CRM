"""Persist capability profiles and rolling metric updates."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from capability_router.models import (
    CapabilityMetrics,
    CapabilityObservation,
    CapabilityProfile,
    CapabilityTaskType,
)
from capability_router.priors import SOFT_CAPABILITY_PRIORS
from db_models.base import new_uuid
from db_models.capability_profiles import (
    CAPABILITY_TASK_TYPES,
    ModelCapabilityObservation,
    ModelCapabilityPrior,
    ModelCapabilityProfile,
)


def _ema(previous: float, value: float, sample_size: int, *, alpha: float | None = None) -> float:
    """Exponential moving average that starts as a plain mean for early samples."""
    if sample_size <= 0:
        return value
    weight = alpha if alpha is not None else min(0.35, 2.0 / (sample_size + 1))
    return (1.0 - weight) * previous + weight * value


class CapabilityProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def seed_soft_priors(self) -> int:
        """Upsert soft priors from code. Never marks them as permanent locks."""
        existing = {
            (row.provider_code, row.model_code, row.task_type): row
            for row in self.session.scalars(select(ModelCapabilityPrior)).all()
        }
        created = 0
        for prior in SOFT_CAPABILITY_PRIORS:
            key = (prior.provider_code, prior.model_code, prior.task_type)
            row = existing.get(key)
            if row is None:
                self.session.add(
                    ModelCapabilityPrior(
                        id=new_uuid(),
                        provider_code=prior.provider_code,
                        model_code=prior.model_code,
                        task_type=prior.task_type,
                        quality_score=prior.quality_score,
                        latency_ms=prior.latency_ms,
                        cost_usd_micros=prior.cost_usd_micros,
                        failure_rate=prior.failure_rate,
                        json_compliance_rate=prior.json_compliance_rate,
                        citation_accuracy=prior.citation_accuracy,
                        historical_agreement=prior.historical_agreement,
                        prior_weight=prior.prior_weight,
                        notes=prior.notes or None,
                    )
                )
                created += 1
            else:
                row.quality_score = prior.quality_score
                row.latency_ms = prior.latency_ms
                row.cost_usd_micros = prior.cost_usd_micros
                row.failure_rate = prior.failure_rate
                row.json_compliance_rate = prior.json_compliance_rate
                row.citation_accuracy = prior.citation_accuracy
                row.historical_agreement = prior.historical_agreement
                row.prior_weight = prior.prior_weight
                row.notes = prior.notes or None
                row.is_active = True
        self.session.commit()
        return created

    def list_priors(self, task_type: str | None = None) -> list[CapabilityProfile]:
        stmt = select(ModelCapabilityPrior).where(ModelCapabilityPrior.is_active.is_(True))
        if task_type:
            stmt = stmt.where(ModelCapabilityPrior.task_type == task_type)
        rows = self.session.scalars(stmt).all()
        return [
            CapabilityProfile(
                id=row.id,
                provider_code=row.provider_code,
                model_code=row.model_code,
                task_type=row.task_type,
                metrics=CapabilityMetrics(
                    quality=row.quality_score,
                    latency_ms=row.latency_ms,
                    cost_usd_micros=float(row.cost_usd_micros),
                    failure_rate=row.failure_rate,
                    json_compliance=row.json_compliance_rate,
                    citation_accuracy=row.citation_accuracy,
                    historical_agreement=row.historical_agreement,
                ),
                sample_size=0,
                source="prior",
                prior_weight=row.prior_weight,
            )
            for row in rows
        ]

    def get_profile(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        provider_code: str,
        model_code: str,
        task_type: str,
    ) -> CapabilityProfile | None:
        row = self.session.scalar(
            select(ModelCapabilityProfile).where(
                ModelCapabilityProfile.organisation_id == organisation_id,
                ModelCapabilityProfile.workspace_id == workspace_id,
                ModelCapabilityProfile.provider_code == provider_code,
                ModelCapabilityProfile.model_code == model_code,
                ModelCapabilityProfile.task_type == task_type,
            )
        )
        return self._to_profile(row) if row else None

    def list_profiles(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        task_type: str | None = None,
    ) -> list[CapabilityProfile]:
        stmt = select(ModelCapabilityProfile).where(
            ModelCapabilityProfile.organisation_id == organisation_id,
            ModelCapabilityProfile.workspace_id == workspace_id,
            ModelCapabilityProfile.status == "active",
        )
        if task_type:
            stmt = stmt.where(ModelCapabilityProfile.task_type == task_type)
        return [self._to_profile(row) for row in self.session.scalars(stmt).all()]

    def record_observation(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        observation: CapabilityObservation,
    ) -> CapabilityProfile:
        task_type = str(observation.task_type)
        if task_type not in CAPABILITY_TASK_TYPES:
            raise ValueError(f"Unsupported task_type: {task_type}")
        try:
            CapabilityTaskType(task_type)
        except ValueError as exc:
            raise ValueError(f"Unsupported task_type: {task_type}") from exc

        profile = self.session.scalar(
            select(ModelCapabilityProfile).where(
                ModelCapabilityProfile.organisation_id == organisation_id,
                ModelCapabilityProfile.workspace_id == workspace_id,
                ModelCapabilityProfile.provider_code == observation.provider_code,
                ModelCapabilityProfile.model_code == observation.model_code,
                ModelCapabilityProfile.task_type == task_type,
            )
        )
        now = datetime.now(UTC)
        if profile is None:
            profile = ModelCapabilityProfile(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                provider_code=observation.provider_code,
                model_code=observation.model_code,
                task_type=task_type,
            )
            self.session.add(profile)
            self.session.flush()

        n = profile.sample_size
        if observation.quality_score is not None:
            profile.quality_score = _ema(profile.quality_score, observation.quality_score, n)
        profile.latency_ms_avg = _ema(profile.latency_ms_avg, observation.latency_ms, n)
        profile.cost_usd_micros_avg = _ema(
            profile.cost_usd_micros_avg, float(observation.cost_usd_micros), n
        )
        if observation.succeeded:
            profile.success_count += 1
        else:
            profile.failure_count += 1
        total = profile.success_count + profile.failure_count
        profile.failure_rate = (profile.failure_count / total) if total else 0.0

        if observation.json_compliant is not None:
            profile.json_compliance_rate = _ema(
                profile.json_compliance_rate,
                1.0 if observation.json_compliant else 0.0,
                n,
            )
        if observation.citation_accuracy is not None:
            profile.citation_accuracy = _ema(
                profile.citation_accuracy, observation.citation_accuracy, n
            )
        if observation.historical_agreement is not None:
            profile.historical_agreement = _ema(
                profile.historical_agreement, observation.historical_agreement, n
            )

        profile.sample_size = n + 1
        profile.last_observed_at = now
        profile.updated_at = now

        self.session.add(
            ModelCapabilityObservation(
                id=observation.id or new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                profile_id=profile.id,
                provider_code=observation.provider_code,
                model_code=observation.model_code,
                task_type=task_type,
                quality_score=observation.quality_score,
                latency_ms=observation.latency_ms,
                cost_usd_micros=observation.cost_usd_micros,
                succeeded=observation.succeeded,
                json_compliant=observation.json_compliant,
                citation_accuracy=observation.citation_accuracy,
                historical_agreement=observation.historical_agreement,
                gateway_role=observation.gateway_role,
                template_id=observation.template_id,
                llm_request_id=observation.llm_request_id,
                notes=observation.notes,
            )
        )
        self.session.commit()
        return self._to_profile(profile)

    @staticmethod
    def _to_profile(row: ModelCapabilityProfile) -> CapabilityProfile:
        return CapabilityProfile(
            id=row.id,
            provider_code=row.provider_code,
            model_code=row.model_code,
            task_type=row.task_type,
            metrics=CapabilityMetrics(
                quality=row.quality_score,
                latency_ms=row.latency_ms_avg,
                cost_usd_micros=row.cost_usd_micros_avg,
                failure_rate=row.failure_rate,
                json_compliance=row.json_compliance_rate,
                citation_accuracy=row.citation_accuracy,
                historical_agreement=row.historical_agreement,
            ),
            sample_size=row.sample_size,
            success_count=row.success_count,
            failure_count=row.failure_count,
            source="observed",
            last_observed_at=row.last_observed_at,
        )
