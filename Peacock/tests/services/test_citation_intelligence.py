from __future__ import annotations

import socket

import pytest

from citation_intelligence import analyse_citation_gaps
from geo_intelligence.models import CitationSignal


def _network_available() -> bool:
    try:
        socket.create_connection(("docs.python.org", 443), timeout=3).close()
        return True
    except OSError:
        return False


@pytest.mark.asyncio
async def test_citation_gap_report_with_no_citations() -> None:
    report = await analyse_citation_gaps(client_brand="Acme", citations=[], client_site_text="Acme text")
    assert report.citations_observed == 0
    assert report.gaps == []


@pytest.mark.asyncio
async def test_citation_gap_reports_unavailable_for_unreachable_url() -> None:
    citations = [
        CitationSignal(
            url="https://this-domain-does-not-exist-abcxyz123.example",
            domain="this-domain-does-not-exist-abcxyz123.example",
            source_class="independent",
            engine_code="chatgpt",
        )
    ]
    report = await analyse_citation_gaps(client_brand="Acme", citations=citations, client_site_text="Acme text", fetch_timeout_seconds=3.0)
    assert report.citations_analysed == 1
    assert report.gaps[0].fetch_status == "fetch_failed"
    assert "Data unavailable" in report.gaps[0].evidence_gap


@pytest.mark.skipif(not _network_available(), reason="No outbound network access in this environment")
@pytest.mark.asyncio
async def test_citation_gap_report_real_fetch() -> None:
    citations = [
        CitationSignal(url="https://docs.python.org/3/", domain="docs.python.org", source_class="independent", engine_code="chatgpt")
    ]
    report = await analyse_citation_gaps(client_brand="Acme", citations=citations, client_site_text="Acme is a widget platform.")
    assert report.gaps[0].fetch_status == "fetched"
    assert report.gaps[0].cited_page_title
