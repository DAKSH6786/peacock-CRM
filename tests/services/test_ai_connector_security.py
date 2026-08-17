"""Peacock Security for AI Connectors — crawler content is DATA."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.ai_connector_security import (
    SECURITY_CONTROLS,
    AiConnectorSecurityScan,
)
from ai_connector_security import (
    AiConnectorSecurityCreateSpec,
    AiConnectorSecurityService,
    SecurityScanSpec,
    analyse_security_scan,
    catalog,
    demo_scan,
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


def test_catalog_policy() -> None:
    c = catalog()
    assert c["security_controls"] == list(SECURITY_CONTROLS)
    assert len(c["security_controls"]) == 8
    assert "DATA" in c["crawler_as_data_policy"]
    assert "not trusted instructions" in c["crawler_as_data_policy"].lower()


def test_demo_blocks_injection_and_treats_crawler_as_data() -> None:
    result = demo_scan("Acme")
    assert result.crawler_treated_as_data is True
    assert result.secrets_exposure_blocked is True
    assert result.system_behaviour_change_blocked is True
    assert result.injection_findings_count >= 3
    assert result.verdict == "quarantine"
    assert all(f.blocked for f in result.injection_findings)
    crawler = next(s for s in result.content_segments if s.segment_key == "crawler_body")
    assert crawler.trust_tier == "untrusted_data"
    assert crawler.treated_as_instructions is False
    assert crawler.isolated is True
    secret = next(
        p for p in result.permission_checks if p.scope_or_connector == "secret_read"
    )
    assert secret.allowed is False
    assert result.url_blocks_count >= 2
    assert result.pii_findings_count >= 1
    kinds = {c.control_kind for c in result.control_activations}
    assert kinds == set(SECURITY_CONTROLS)


def test_clean_content_allows() -> None:
    result = analyse_security_scan(
        SecurityScanSpec(
            client_brand="Acme",
            crawler_content="<html><body><p>Acme pricing starts at $49/mo.</p></body></html>",
            candidate_urls=["https://acme.example/pricing"],
            requested_tool_scopes=["read_visibility"],
            granted_tool_scopes=["read_visibility"],
            model_output="Structured summary: pricing page is informational.",
        )
    )
    assert result.injection_findings_count == 0
    assert result.verdict in ("allow", "allow_with_redactions")
    assert result.crawler_treated_as_data is True


def test_cross_tenant_claim_fails() -> None:
    result = analyse_security_scan(
        SecurityScanSpec(
            client_brand="Acme",
            crawler_content="<p>Hello</p>",
            organisation_id="org_a",
            workspace_id="ws_a",
            claimed_organisation_id="org_b",
            candidate_urls=["https://acme.example/"],
            model_output="Structured summary: ok.",
        )
    )
    assert result.tenant_boundary_ok is False


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_security_scan() -> None:
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
            name=f"acs-{suffix}",
            slug=f"acs-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"acs-{suffix}.com",
            root_url=f"https://acs-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = AiConnectorSecurityService(db).scan(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=AiConnectorSecurityCreateSpec(
                website_id=website.id,
                name=f"ACS {suffix}",
                scan=SecurityScanSpec(client_brand="Acme"),
            ),
        )
        assert report.result.crawler_treated_as_data is True
        row = db.scalar(
            select(AiConnectorSecurityScan).where(
                AiConnectorSecurityScan.id == report.scan_id
            )
        )
        assert row is not None
        assert row.secrets_exposure_blocked is True

        loaded = AiConnectorSecurityService(db).get_scan(
            scan_id=report.scan_id, organisation_id=org.id
        )
        assert loaded is not None
        assert loaded.result.injection_findings_count >= 1
    finally:
        db.close()
