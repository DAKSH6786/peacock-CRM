"""Peacock GEO Lab orchestration — controlled experiments with cautious causality."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.geo_lab import (
    CAUSALITY_WARNING,
    METHODOLOGY,
    GlCausalityAssessment,
    GlMetricDelta,
    GlMetricObservation,
    GlPage,
    GlVariant,
    GeoLabExperiment,
)
from geo_lab.analysis import (
    CausalityAssessmentResult,
    ExperimentAnalysisInput,
    MetricDeltaResult,
    ObservationSpec,
    PageSpec,
    TimeSeriesPoint,
    VariantSpec,
    analyse_experiment,
    default_variants,
)
from geo_lab.models import GeoLabReport, GeoLabSpec


class GeoLabService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_experiment(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: GeoLabSpec,
        created_by: str | None = None,
    ) -> GeoLabReport:
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")
        if not spec.hypothesis.strip():
            raise ValueError("hypothesis is required")
        if not spec.pages:
            raise ValueError("At least one control or test page is required")
        if not spec.observations:
            raise ValueError("At least one metric observation is required")

        variants = list(spec.variants)
        if not variants and spec.use_default_variants_if_empty:
            variants = default_variants()
        if not variants:
            raise ValueError("At least one variant is required")

        analysis = analyse_experiment(
            ExperimentAnalysisInput(
                variants=variants,
                pages=spec.pages,
                observations=spec.observations,
                known_confounds=spec.known_confounds,
                concurrent_changes=spec.concurrent_changes,
            )
        )

        has_control = any(p.page_role == "control" for p in spec.pages)
        has_matched = any(p.matched_group for p in spec.pages)
        has_ts = "time_series" in analysis.design_features

        experiment = GeoLabExperiment(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.client_brand.strip(),
            topic_cluster=spec.topic_cluster,
            hypothesis=spec.hypothesis.strip(),
            experiment_status="analysed",
            design_type=spec.design_type,
            pre_window_start=spec.pre_window_start,
            pre_window_end=spec.pre_window_end,
            post_window_start=spec.post_window_start,
            post_window_end=spec.post_window_end,
            intervention_date=spec.intervention_date,
            has_control_pages=has_control,
            has_matched_groups=has_matched,
            has_time_series=has_ts,
            causality_warning=CAUSALITY_WARNING,
            overall_causality_level=analysis.overall_causality_level,
            overall_summary=analysis.overall_summary,
            methodology=METHODOLOGY,
            notes=spec.notes,
        )
        self.db.add(experiment)
        self.db.flush()

        variant_id_by_code: dict[str, str] = {}
        variant_rows: list[dict] = []
        for v in variants:
            row = GlVariant(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                experiment_id=experiment.id,
                variant_code=v.variant_code,
                label=v.resolved_label(),
                treatment_description=v.resolved_treatment(),
                is_baseline=v.is_baseline or v.variant_code.upper() == "A",
                change_summary=v.change_summary,
            )
            self.db.add(row)
            self.db.flush()
            variant_id_by_code[v.variant_code] = row.id
            variant_rows.append(
                {
                    "variant_id": row.id,
                    "variant_code": row.variant_code,
                    "label": row.label,
                    "treatment_description": row.treatment_description,
                    "is_baseline": row.is_baseline,
                    "change_summary": row.change_summary,
                }
            )

        page_id_by_url: dict[str, str] = {}
        page_rows: list[dict] = []
        for p in spec.pages:
            vid = variant_id_by_code.get(p.variant_code) if p.variant_code else None
            row = GlPage(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                experiment_id=experiment.id,
                variant_id=vid,
                url=p.url,
                title=p.title,
                page_role=p.page_role,
                matched_group=p.matched_group,
                match_key=p.match_key,
            )
            self.db.add(row)
            self.db.flush()
            page_id_by_url[p.url] = row.id
            page_rows.append(
                {
                    "page_id": row.id,
                    "url": row.url,
                    "title": row.title,
                    "page_role": row.page_role,
                    "variant_code": p.variant_code,
                    "matched_group": row.matched_group,
                    "match_key": row.match_key,
                }
            )

        for o in spec.observations:
            page_id = page_id_by_url.get(o.page_url)
            if page_id is None:
                raise ValueError(f"Observation references unknown page_url: {o.page_url}")
            self.db.add(
                GlMetricObservation(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    experiment_id=experiment.id,
                    page_id=page_id,
                    metric_code=o.metric_code,
                    observed_at=o.observed_at,
                    period=o.period,
                    value=o.value,
                    engine=o.engine,
                    notes=o.notes,
                )
            )

        for d in analysis.deltas:
            self.db.add(
                GlMetricDelta(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    experiment_id=experiment.id,
                    scope_type=d.scope_type,
                    scope_id=d.scope_id[:64],
                    metric_code=d.metric_code,
                    pre_mean=d.pre_mean,
                    post_mean=d.post_mean,
                    absolute_delta=d.absolute_delta,
                    relative_delta_pct=d.relative_delta_pct,
                    control_adjusted_delta=d.control_adjusted_delta,
                    observation_count_pre=d.observation_count_pre,
                    observation_count_post=d.observation_count_post,
                )
            )

        for c in analysis.causality_assessments:
            self.db.add(
                GlCausalityAssessment(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    experiment_id=experiment.id,
                    metric_code=c.metric_code,
                    variant_code=c.variant_code,
                    causality_level=c.causality_level,
                    claim_allowed=c.claim_allowed,
                    auto_causal_conclusion_rejected=True,
                    rationale=c.rationale,
                    confounds_noted=c.confounds_noted,
                    design_supports=",".join(c.design_supports),
                    confidence_note=c.confidence_note,
                )
            )

        self.db.commit()

        return GeoLabReport(
            experiment_id=experiment.id,
            name=experiment.name,
            client_brand=experiment.client_brand,
            hypothesis=experiment.hypothesis,
            methodology=experiment.methodology,
            design_type=experiment.design_type,
            design_features=analysis.design_features,
            causality_warning=CAUSALITY_WARNING,
            overall_causality_level=analysis.overall_causality_level,
            overall_summary=analysis.overall_summary,
            variants=variant_rows,
            pages=page_rows,
            deltas=analysis.deltas,
            causality_assessments=analysis.causality_assessments,
            time_series=analysis.time_series,
            auto_causal_conclusion_rejected=True,
            analysis=analysis,
        )

    def get_experiment(
        self, *, experiment_id: str, organisation_id: str
    ) -> GeoLabReport | None:
        experiment = self.db.scalar(
            select(GeoLabExperiment).where(
                GeoLabExperiment.id == experiment_id,
                GeoLabExperiment.organisation_id == organisation_id,
            )
        )
        if experiment is None:
            return None

        variants = list(
            self.db.scalars(
                select(GlVariant).where(GlVariant.experiment_id == experiment.id)
            ).all()
        )
        pages = list(
            self.db.scalars(
                select(GlPage).where(GlPage.experiment_id == experiment.id)
            ).all()
        )
        variant_code_by_id = {v.id: v.variant_code for v in variants}
        deltas = [
            MetricDeltaResult(
                scope_type=d.scope_type,
                scope_id=d.scope_id,
                metric_code=d.metric_code,
                pre_mean=d.pre_mean,
                post_mean=d.post_mean,
                absolute_delta=d.absolute_delta,
                relative_delta_pct=d.relative_delta_pct,
                control_adjusted_delta=d.control_adjusted_delta,
                observation_count_pre=d.observation_count_pre,
                observation_count_post=d.observation_count_post,
            )
            for d in self.db.scalars(
                select(GlMetricDelta).where(GlMetricDelta.experiment_id == experiment.id)
            ).all()
        ]
        assessments = [
            CausalityAssessmentResult(
                metric_code=c.metric_code,
                variant_code=c.variant_code,
                causality_level=c.causality_level,
                claim_allowed=c.claim_allowed,
                auto_causal_conclusion_rejected=c.auto_causal_conclusion_rejected,
                rationale=c.rationale,
                confounds_noted=c.confounds_noted,
                design_supports=[x for x in (c.design_supports or "").split(",") if x],
                confidence_note=c.confidence_note,
            )
            for c in self.db.scalars(
                select(GlCausalityAssessment).where(
                    GlCausalityAssessment.experiment_id == experiment.id
                )
            ).all()
        ]

        # Rebuild coarse time series from observations
        obs = list(
            self.db.scalars(
                select(GlMetricObservation).where(
                    GlMetricObservation.experiment_id == experiment.id
                )
            ).all()
        )
        page_role = {p.id: p.page_role for p in pages}
        from collections import defaultdict
        from statistics import mean

        bucket: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
        for o in obs:
            bucket[
                (o.observed_at, o.period, o.metric_code, page_role.get(o.page_id, "unknown"))
            ].append(o.value)
        time_series = [
            TimeSeriesPoint(
                observed_at=k[0],
                period=k[1],
                metric_code=k[2],
                scope_type="page_role",
                scope_id=k[3],
                value=float(mean(vals)),
            )
            for k, vals in sorted(bucket.items())
        ]

        design_features: list[str] = ["before_after"]
        if experiment.has_control_pages:
            design_features.append("control_pages")
        if any(p.page_role == "test" for p in pages):
            design_features.append("test_pages")
        if experiment.has_matched_groups:
            design_features.append("matched_groups")
        if experiment.has_time_series:
            design_features.append("time_series")

        return GeoLabReport(
            experiment_id=experiment.id,
            name=experiment.name,
            client_brand=experiment.client_brand,
            hypothesis=experiment.hypothesis,
            methodology=experiment.methodology,
            design_type=experiment.design_type,
            design_features=design_features,
            causality_warning=experiment.causality_warning,
            overall_causality_level=experiment.overall_causality_level,
            overall_summary=experiment.overall_summary or "",
            variants=[
                {
                    "variant_id": v.id,
                    "variant_code": v.variant_code,
                    "label": v.label,
                    "treatment_description": v.treatment_description,
                    "is_baseline": v.is_baseline,
                    "change_summary": v.change_summary,
                }
                for v in variants
            ],
            pages=[
                {
                    "page_id": p.id,
                    "url": p.url,
                    "title": p.title,
                    "page_role": p.page_role,
                    "variant_code": variant_code_by_id.get(p.variant_id or ""),
                    "matched_group": p.matched_group,
                    "match_key": p.match_key,
                }
                for p in pages
            ],
            deltas=deltas,
            causality_assessments=assessments,
            time_series=time_series,
            auto_causal_conclusion_rejected=True,
        )
