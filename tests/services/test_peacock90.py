"""Peacock 90 2.0 — adaptive optimisation + dependency graph."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.peacock90 import P90Dependency, P90Initiative, Peacock90Plan
from peacock90 import (
    CAPACITY_GUARDRAIL,
    PlanSpec,
    ResourceConstraints,
    optimise_roadmap,
)
from peacock90.models import Peacock90Spec
from peacock90.service import Peacock90Service


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


def _example_constraints(**overrides) -> ResourceConstraints:
    base = dict(
        budget_amount=400_000.0,
        budget_currency="INR",
        writers=5,
        developers=2,
        seo_specialists=1,
        articles_per_month_max=25,
        approval_capacity_per_week=8,
        business_priorities=["technical_seo", "content", "authority"],
        risk_tolerance="medium",
    )
    base.update(overrides)
    return ResourceConstraints(**base)


def test_does_not_recommend_100_articles_when_capacity_is_25() -> None:
    result = optimise_roadmap(
        PlanSpec(client_brand="Acme", constraints=_example_constraints())
    )
    assert result.capacity_guardrail
    assert any(r.requested_amount >= 100 for r in result.capacity_refusals)
    assert all(
        i.articles_required <= 25 * 3 for i in result.initiatives if i.selected
    )
    assert result.articles_planned <= 25 * 3

    # Even with high risk tolerance, 100-article blast must be refused on capacity
    high_risk = optimise_roadmap(
        PlanSpec(
            client_brand="Acme",
            constraints=_example_constraints(risk_tolerance="high"),
        )
    )
    mega = next(
        i for i in high_risk.initiatives if i.initiative_code == "mega_content_blast"
    )
    assert mega.selected is False
    assert mega.rejection_reason
    assert (
        "100" in mega.rejection_reason
        or "capacity" in mega.rejection_reason.lower()
        or "articles" in mega.rejection_reason.lower()
    )
    assert all(
        i.articles_required <= 25 * 3 for i in high_risk.initiatives if i.selected
    )


def test_dependency_graph_canonical_chain() -> None:
    result = optimise_roadmap(
        PlanSpec(client_brand="Acme", constraints=_example_constraints())
    )
    assert result.dependency_example == [
        "Fix canonical issue",
        "Recrawl",
        "Update content",
        "Request indexing",
        "Monitor",
    ]
    chain = next(
        (i for i in result.initiatives if i.initiative_code == "fix_canonical_chain"),
        None,
    )
    assert chain is not None
    assert chain.selected is True

    titles = {t.title: t for t in result.tasks if t.initiative_code == "fix_canonical_chain"}
    assert set(titles) >= {
        "Fix canonical issue",
        "Recrawl",
        "Update content",
        "Request indexing",
        "Monitor",
    }
    # Dependency edges exist in order
    codes = {t.title: t.task_code for t in titles.values()}
    edges = {(d.predecessor_task_code, d.successor_task_code) for d in result.dependencies}
    assert (codes["Fix canonical issue"], codes["Recrawl"]) in edges
    assert (codes["Recrawl"], codes["Update content"]) in edges
    assert (codes["Update content"], codes["Request indexing"]) in edges
    assert (codes["Request indexing"], codes["Monitor"]) in edges

    # Weeks respect dependency order
    assert titles["Fix canonical issue"].week_index <= titles["Recrawl"].week_index
    assert titles["Recrawl"].week_index <= titles["Update content"].week_index
    assert titles["Update content"].week_index <= titles["Request indexing"].week_index
    assert titles["Request indexing"].week_index <= titles["Monitor"].week_index


def test_respects_budget_and_headcount() -> None:
    tight = optimise_roadmap(
        PlanSpec(
            client_brand="Acme",
            constraints=_example_constraints(
                budget_amount=50_000.0,
                writers=1,
                developers=1,
                seo_specialists=1,
                articles_per_month_max=5,
            ),
        )
    )
    rich = optimise_roadmap(
        PlanSpec(client_brand="Acme", constraints=_example_constraints(budget_amount=800_000.0))
    )
    assert tight.budget_used <= 50_000.0 + 1e-6
    assert tight.initiatives_selected <= rich.initiatives_selected
    assert tight.articles_planned <= 5 * 3


def test_low_risk_tolerance_filters_high_risk() -> None:
    result = optimise_roadmap(
        PlanSpec(
            client_brand="Acme",
            constraints=_example_constraints(risk_tolerance="low"),
        )
    )
    selected = [i for i in result.initiatives if i.selected]
    assert all(i.risk_level == "low" for i in selected)


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_peacock90_plan() -> None:
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
            name=f"p90-{suffix}",
            slug=f"p90-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"p90-{suffix}.com",
            root_url=f"https://p90-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = Peacock90Service(db).generate(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=Peacock90Spec(
                website_id=website.id,
                name=f"90d plan {suffix}",
                plan=PlanSpec(
                    client_brand="Acme",
                    constraints=_example_constraints(),
                ),
            ),
        )
        assert report.plan_id
        assert report.result.initiatives_selected >= 1
        row = db.scalar(select(Peacock90Plan).where(Peacock90Plan.id == report.plan_id))
        assert row is not None
        assert row.articles_per_month_max == 25
        deps = list(
            db.scalars(
                select(P90Dependency).where(P90Dependency.plan_id == report.plan_id)
            ).all()
        )
        assert deps
        mega = db.scalar(
            select(P90Initiative).where(
                P90Initiative.plan_id == report.plan_id,
                P90Initiative.initiative_code == "mega_content_blast",
            )
        )
        assert mega is not None
        assert mega.selected is False

        loaded = Peacock90Service(db).get_plan(
            plan_id=report.plan_id, organisation_id=org.id
        )
        assert loaded is not None
        assert loaded.result.tasks_scheduled == report.result.tasks_scheduled
    finally:
        db.close()
