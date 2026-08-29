"""Peacock GEO Lab — controlled experiments and cautious causality."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.geo_lab import GlCausalityAssessment, GeoLabExperiment
from geo_lab import (
    CAUSALITY_LEVELS,
    CAUSALITY_WARNING,
    GEO_LAB_METRICS,
    VARIANT_PRESETS,
    GeoLabService,
    GeoLabSpec,
    ObservationSpec,
    PageSpec,
    VariantSpec,
    analyse_experiment,
    classify_causality,
    default_variants,
)
from geo_lab.analysis import ExperimentAnalysisInput


def _database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://peacock:peacock@localhost:5432/peacock_one",
    )


def _can_connect() -> bool:
    try:
        engine = create_engine(_database_url())
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False


def test_variant_presets_and_metrics() -> None:
    assert VARIANT_PRESETS["A"] == "original_page"
    assert VARIANT_PRESETS["B"] == "improved_evidence"
    assert VARIANT_PRESETS["C"] == "better_structured_answers"
    assert VARIANT_PRESETS["D"] == "original_dataset_added"
    assert set(GEO_LAB_METRICS) == {
        "seo",
        "retrieval",
        "ai_mention",
        "ai_citation",
        "answer_prominence",
        "organic_performance",
    }
    assert CAUSALITY_LEVELS == (
        "correlation",
        "likely_contribution",
        "controlled_experiment",
        "causal_evidence",
    )
    assert "CAUSALITY WARNING" in CAUSALITY_WARNING
    assert "does NOT automatically conclude" in CAUSALITY_WARNING


def test_default_variants_abcd() -> None:
    variants = default_variants()
    assert [v.variant_code for v in variants] == ["A", "B", "C", "D"]
    assert variants[0].is_baseline is True


def test_never_auto_concludes_causation() -> None:
    result = classify_causality(
        metric_code="ai_citation",
        variant_code="B",
        test_delta=0.25,
        control_delta=0.02,
        control_adjusted_delta=0.23,
        design_features=[
            "before_after",
            "control_pages",
            "test_pages",
            "matched_groups",
            "time_series",
        ],
        n_pre=4,
        n_post=4,
        known_confounds=[],
        concurrent_changes=[],
    )
    assert result.auto_causal_conclusion_rejected is True
    assert result.causality_level in CAUSALITY_LEVELS
    # Even at causal_evidence, must not authorize automatic "X caused Y"
    assert "does NOT" in result.rationale or "not" in result.confidence_note.lower()


def test_no_control_caps_at_correlation_or_weak() -> None:
    result = classify_causality(
        metric_code="seo",
        variant_code="C",
        test_delta=0.4,
        control_delta=None,
        control_adjusted_delta=None,
        design_features=["before_after", "test_pages"],
        n_pre=3,
        n_post=3,
        known_confounds=[],
        concurrent_changes=[],
    )
    assert result.causality_level in ("correlation", "likely_contribution")
    assert result.causality_level != "causal_evidence"
    assert result.auto_causal_conclusion_rejected is True


def test_controlled_experiment_with_controls_and_series() -> None:
    pages = [
        PageSpec(
            url="https://ex.com/control",
            page_role="control",
            variant_code="A",
            matched_group="g1",
            match_key="crm",
        ),
        PageSpec(
            url="https://ex.com/test-b",
            page_role="test",
            variant_code="B",
            matched_group="g1",
            match_key="crm",
        ),
    ]
    observations: list[ObservationSpec] = []
    for metric in GEO_LAB_METRICS:
        # Control stays flat
        observations.append(
            ObservationSpec(
                page_url="https://ex.com/control",
                metric_code=metric,
                observed_at="2026-01-01",
                period="pre",
                value=0.40,
            )
        )
        observations.append(
            ObservationSpec(
                page_url="https://ex.com/control",
                metric_code=metric,
                observed_at="2026-01-08",
                period="pre",
                value=0.41,
            )
        )
        observations.append(
            ObservationSpec(
                page_url="https://ex.com/control",
                metric_code=metric,
                observed_at="2026-02-01",
                period="post",
                value=0.42,
            )
        )
        observations.append(
            ObservationSpec(
                page_url="https://ex.com/control",
                metric_code=metric,
                observed_at="2026-02-08",
                period="post",
                value=0.41,
            )
        )
        # Test (improved evidence) rises
        observations.append(
            ObservationSpec(
                page_url="https://ex.com/test-b",
                metric_code=metric,
                observed_at="2026-01-01",
                period="pre",
                value=0.40,
            )
        )
        observations.append(
            ObservationSpec(
                page_url="https://ex.com/test-b",
                metric_code=metric,
                observed_at="2026-01-08",
                period="pre",
                value=0.39,
            )
        )
        observations.append(
            ObservationSpec(
                page_url="https://ex.com/test-b",
                metric_code=metric,
                observed_at="2026-02-01",
                period="post",
                value=0.62,
            )
        )
        observations.append(
            ObservationSpec(
                page_url="https://ex.com/test-b",
                metric_code=metric,
                observed_at="2026-02-08",
                period="post",
                value=0.65,
            )
        )

    result = analyse_experiment(
        ExperimentAnalysisInput(
            variants=default_variants(),
            pages=pages,
            observations=observations,
        )
    )
    assert "control_pages" in result.design_features
    assert "matched_groups" in result.design_features
    assert "time_series" in result.design_features
    assert "before_after" in result.design_features
    assert result.causality_warning == CAUSALITY_WARNING
    assert all(a.auto_causal_conclusion_rejected for a in result.causality_assessments)
    assert result.overall_causality_level in (
        "likely_contribution",
        "controlled_experiment",
        "causal_evidence",
    )
    # Test AI citation should show positive control-adjusted lift
    cit = next(
        d
        for d in result.deltas
        if d.scope_type == "variant" and d.scope_id == "B" and d.metric_code == "ai_citation"
    )
    assert cit.absolute_delta > 0.1
    assert cit.control_adjusted_delta is not None
    assert cit.control_adjusted_delta > 0.1
    assert len(result.time_series) > 0


def test_confounds_downgrade_causal_evidence() -> None:
    result = classify_causality(
        metric_code="ai_mention",
        variant_code="D",
        test_delta=0.3,
        control_delta=0.01,
        control_adjusted_delta=0.29,
        design_features=[
            "before_after",
            "control_pages",
            "test_pages",
            "matched_groups",
            "time_series",
        ],
        n_pre=4,
        n_post=4,
        known_confounds=["algorithm update week"],
        concurrent_changes=["sitewide title rewrite"],
    )
    assert result.causality_level in (
        "correlation",
        "likely_contribution",
        "controlled_experiment",
    )
    assert result.causality_level != "causal_evidence"
    assert result.auto_causal_conclusion_rejected is True
    assert result.confounds_noted is not None


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_geo_lab_persists() -> None:
    engine = create_engine(_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        org = db.scalar(select(Organisation).limit(1))
        if org is None:
            pytest.skip("Seed organisation required")
        suffix = new_uuid()[:8]
        workspace = Workspace(
            id=new_uuid(),
            organisation_id=org.id,
            name=f"gl-{suffix}",
            slug=f"gl-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"gl-{suffix}.com",
            root_url=f"https://gl-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = GeoLabService(db).run_experiment(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=GeoLabSpec(
                website_id=website.id,
                name=f"GEO {suffix}",
                client_brand="Peacock",
                hypothesis="Improved evidence increases AI citation vs control",
                pages=[
                    PageSpec(
                        url=f"https://gl-{suffix}.com/control",
                        page_role="control",
                        variant_code="A",
                        matched_group="m1",
                    ),
                    PageSpec(
                        url=f"https://gl-{suffix}.com/test",
                        page_role="test",
                        variant_code="B",
                        matched_group="m1",
                    ),
                ],
                observations=[
                    ObservationSpec(
                        page_url=f"https://gl-{suffix}.com/control",
                        metric_code="ai_citation",
                        observed_at="2026-01-01",
                        period="pre",
                        value=0.3,
                    ),
                    ObservationSpec(
                        page_url=f"https://gl-{suffix}.com/control",
                        metric_code="ai_citation",
                        observed_at="2026-02-01",
                        period="post",
                        value=0.31,
                    ),
                    ObservationSpec(
                        page_url=f"https://gl-{suffix}.com/test",
                        metric_code="ai_citation",
                        observed_at="2026-01-01",
                        period="pre",
                        value=0.3,
                    ),
                    ObservationSpec(
                        page_url=f"https://gl-{suffix}.com/test",
                        metric_code="ai_citation",
                        observed_at="2026-02-01",
                        period="post",
                        value=0.55,
                    ),
                ],
                variants=[],
                use_default_variants_if_empty=True,
            ),
        )
        assert report.auto_causal_conclusion_rejected is True
        assert "CAUSALITY WARNING" in report.causality_warning
        exp = db.scalar(
            select(GeoLabExperiment).where(
                GeoLabExperiment.id == report.experiment_id
            )
        )
        assert exp is not None
        assessments = list(
            db.scalars(
                select(GlCausalityAssessment).where(
                    GlCausalityAssessment.experiment_id == report.experiment_id
                )
            ).all()
        )
        assert assessments
        assert all(a.auto_causal_conclusion_rejected for a in assessments)
    finally:
        db.close()
