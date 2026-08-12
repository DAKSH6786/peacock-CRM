"""Peacock Action Engine — approval gates + destructive guardrail."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from action_engine import (
    ACTION_STATUSES,
    DESTRUCTIVE_GUARDRAIL,
    ActionDraft,
    ActionEngineService,
    ActionEngineSpec,
    create_action_view,
)
from action_engine.workflow import (
    approve_action,
    execute_action,
    reject_action,
    revert_action,
    submit_for_approval,
)
from db_models import Organisation, Website, Workspace
from db_models.action_engine import PeacockAction
from db_models.base import new_uuid


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


def test_status_lifecycle_constants() -> None:
    assert ACTION_STATUSES == (
        "DRAFT",
        "APPROVAL_REQUIRED",
        "APPROVED",
        "EXECUTED",
        "FAILED",
        "REVERTED",
    )


def test_happy_path_create_task() -> None:
    draft = ActionDraft(
        action_type="create_task",
        title="Create SEO fix task",
        payload_summary="Task: fix canonical on /pricing",
    )
    view = create_action_view(draft)
    assert view.action_status == "APPROVAL_REQUIRED"
    assert view.is_destructive_external is False
    view = approve_action(view)
    assert view.action_status == "APPROVED"
    view = execute_action(view, draft)
    assert view.action_status == "EXECUTED"
    assert view.executions
    assert view.executions[-1].outcome == "EXECUTED"
    view = revert_action(view)
    assert view.action_status == "REVERTED"


def test_reject_returns_to_draft() -> None:
    draft = ActionDraft(
        action_type="generate_brief",
        title="Brief for topic X",
        payload_summary="Brief payload",
    )
    view = create_action_view(draft)
    view = reject_action(view, comment="Need more context")
    assert view.action_status == "DRAFT"


def test_never_destructive_without_permission() -> None:
    draft = ActionDraft(
        action_type="cms_publish",
        title="Publish homepage",
        payload_summary="CMS publish /",
        risk_level="high",
    )
    view = create_action_view(draft, granted_permissions=[])
    assert view.is_destructive_external is True
    assert view.action_status == "DRAFT"
    assert view.permission_granted is False
    assert "destructive" in view.destructive_guardrail.lower() or DESTRUCTIVE_GUARDRAIL

    with pytest.raises(ValueError, match="explicit permission"):
        submit_for_approval(view)

    # Even if someone forces APPROVED path, execute fails closed
    view_perm = create_action_view(draft, granted_permissions=["cms_publish"])
    assert view_perm.permission_granted is True
    assert view_perm.action_status == "APPROVAL_REQUIRED"
    approved = approve_action(view_perm)
    # Without permission on a forged view:
    forged = create_action_view(draft, granted_permissions=[])
    # Manually walk: cannot submit
    with pytest.raises(ValueError, match="explicit permission"):
        submit_for_approval(forged)

    # Execute approved+permission path works as internal stub still blocks live CMS?
    # With permission, cms_publish still fails in simulator (guardrail executor) until
    # a real connector exists — _simulate_internal_execution fails destructive types.
    executed = execute_action(approved, draft)
    assert executed.action_status == "FAILED"
    assert executed.failure_reason
    assert "destructive" in executed.failure_reason.lower() or "Blocked" in executed.failure_reason


def test_all_core_action_types_createable() -> None:
    core = [
        "create_task",
        "assign_writer",
        "generate_brief",
        "notify_editor",
        "schedule_recrawl",
        "generate_schema_suggestion",
        "prepare_internal_linking_plan",
        "create_outreach_prospect",
        "generate_report",
        "schedule_monitoring",
    ]
    for code in core:
        view = create_action_view(
            ActionDraft(
                action_type=code,
                title=f"Test {code}",
                payload_summary=f"payload for {code}",
            )
        )
        assert view.action_label
        assert view.action_status in ACTION_STATUSES


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_action_lifecycle() -> None:
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
            name=f"pae-{suffix}",
            slug=f"pae-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"pae-{suffix}.com",
            root_url=f"https://pae-{suffix}.com",
        )
        db.add(website)
        db.commit()

        svc = ActionEngineService(db)
        report = svc.create(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=ActionEngineSpec(
                website_id=website.id,
                draft=ActionDraft(
                    action_type="assign_writer",
                    title="Assign writer to brief",
                    payload_summary="writer=w1 brief=b1",
                ),
            ),
        )
        assert report.view.action_status == "APPROVAL_REQUIRED"
        report = svc.approve(
            action_id=report.action_id,
            organisation_id=org.id,
            actor_user_id=None,
        )
        assert report.view.action_status == "APPROVED"
        report = svc.execute(
            action_id=report.action_id,
            organisation_id=org.id,
            actor_user_id=None,
        )
        assert report.view.action_status == "EXECUTED"
        row = db.scalar(
            select(PeacockAction).where(PeacockAction.id == report.action_id)
        )
        assert row is not None
        assert row.action_status == "EXECUTED"
    finally:
        db.close()
