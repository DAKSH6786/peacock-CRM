"""Peacock Command Centre — Visibility Index, situation, intelligence feed."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from command_centre import (
    VISIBILITY_DIMENSIONS,
    CommandCentreSpec,
    assemble_command_centre,
    catalog,
)
from command_centre.models import CommandCentreCreateSpec
from command_centre.service import CommandCentreService
from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.command_centre import CommandCentreSnapshot


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


def test_catalog_and_dimensions() -> None:
    c = catalog()
    assert set(c["visibility_dimensions"]) == set(VISIBILITY_DIMENSIONS)
    assert "biggest_opportunity" in c["situation_kinds"]
    assert "SEO dashboard" in c["product_note"] or "not a generic SEO" in c["product_note"]


def test_demo_assembly_has_index_situation_feed() -> None:
    result = assemble_command_centre(CommandCentreSpec(client_brand="Acme"))
    assert result.visibility_index > 0
    assert len(result.signals) == 7
    assert {s.dimension for s in result.signals} == set(VISIBILITY_DIMENSIONS)
    assert len(result.situations) == 6
    assert result.feed_items
    top = result.feed_items[0]
    assert top.detection_label == "PEACOCK DETECTED"
    assert "18%" in top.body and "31%" in top.body
    assert top.primary_driver
    assert top.potential_response
    assert abs(top.confidence - 0.87) < 0.001


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_command_centre_snapshot() -> None:
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
            name=f"cc-{suffix}",
            slug=f"cc-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"cc-{suffix}.com",
            root_url=f"https://cc-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = CommandCentreService(db).create_snapshot(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=CommandCentreCreateSpec(
                website_id=website.id,
                name=f"CC {suffix}",
                centre=CommandCentreSpec(client_brand="Acme"),
            ),
        )
        assert report.snapshot_id
        row = db.scalar(
            select(CommandCentreSnapshot).where(
                CommandCentreSnapshot.id == report.snapshot_id
            )
        )
        assert row is not None
        assert row.visibility_index == report.result.visibility_index
    finally:
        db.close()
