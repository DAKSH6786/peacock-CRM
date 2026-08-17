"""Peacock Enterprise Reliability — partial multi-provider reports."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.enterprise_reliability import (
    RELIABILITY_CONTROLS,
    EnterpriseReliabilityRun,
)
from enterprise_reliability import (
    EnterpriseReliabilityCreateSpec,
    EnterpriseReliabilityService,
    ReliabilityRunSpec,
    analyse_reliability_run,
    catalog,
    demo_run,
)


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


def test_catalog_lists_all_controls() -> None:
    c = catalog()
    assert c["reliability_controls"] == list(RELIABILITY_CONTROLS)
    assert len(c["reliability_controls"]) == 11
    assert "idempotent_jobs" in c["reliability_controls"]
    assert "partial_results" in c["reliability_controls"]
    assert "4/5" in c["example_partial_summary"]
    assert "DeepSeek" in c["example_partial_summary"]


def test_demo_four_of_five_deepseek_unavailable() -> None:
    result = demo_run("Acme")
    assert result.engines_attempted == 5
    assert result.engines_succeeded == 4
    assert result.engines_failed == 1
    assert result.report_status == "completed_partial"
    assert result.partial_result_summary == (
        "4/5 AI engines successfully measured. DeepSeek unavailable during this run."
    )
    assert "deepseek" in result.unavailable_providers
    deepseek = next(p for p in result.provider_measurements if p.engine_code == "deepseek")
    assert deepseek.outcome == "unavailable"
    assert deepseek.included_in_report is False
    assert result.dlq_events_count >= 1
    open_circuits = [c for c in result.circuit_states if c.circuit_state == "open"]
    assert any(c.provider_code == "deepseek" for c in open_circuits)
    kinds = {c.control_kind for c in result.control_activations}
    assert kinds == set(RELIABILITY_CONTROLS)


def test_all_engines_succeed_is_completed() -> None:
    result = analyse_reliability_run(
        ReliabilityRunSpec(
            client_brand="Acme",
            unavailable_engines=[],
        )
    )
    assert result.engines_succeeded == 5
    assert result.report_status == "completed"
    assert "5/5" in result.partial_result_summary


def test_cancellation_stops_run() -> None:
    result = analyse_reliability_run(
        ReliabilityRunSpec(
            client_brand="Acme",
            cancel_requested=True,
            idempotency_key="cancel-demo",
        )
    )
    assert result.cancelled is True
    assert result.report_status == "cancelled"
    assert all(p.outcome == "cancelled" for p in result.provider_measurements)


def test_workflow_recovery_checkpoint() -> None:
    result = analyse_reliability_run(
        ReliabilityRunSpec(
            client_brand="Acme",
            unavailable_engines=["deepseek"],
            recover_from_checkpoint=True,
        )
    )
    assert result.recovered_from_checkpoint is True
    assert any(w.phase == "recovered" for w in result.workflow_checkpoints)


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_reliability_run() -> None:
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
            name=f"er-{suffix}",
            slug=f"er-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"er-{suffix}.com",
            root_url=f"https://er-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = EnterpriseReliabilityService(db).run(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=EnterpriseReliabilityCreateSpec(
                website_id=website.id,
                name=f"ER {suffix}",
                run=ReliabilityRunSpec(
                    client_brand="Acme",
                    unavailable_engines=["deepseek"],
                    idempotency_key=f"er-{suffix}",
                ),
            ),
        )
        assert report.result.engines_succeeded == 4
        row = db.scalar(
            select(EnterpriseReliabilityRun).where(
                EnterpriseReliabilityRun.id == report.run_id
            )
        )
        assert row is not None
        assert "4/5" in row.partial_result_summary
        assert "DeepSeek" in row.partial_result_summary

        loaded = EnterpriseReliabilityService(db).get_run(
            run_id=report.run_id, organisation_id=org.id
        )
        assert loaded is not None
        assert loaded.result.engines_succeeded == 4
        assert len(loaded.result.control_activations) == 11
    finally:
        db.close()
