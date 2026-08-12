"""Peacock SEO Engine service facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from crawler.store import StoredCrawl
from seo_engine.engine import PeacockSeoEngine
from seo_engine.models import SeoAuditReport


@dataclass
class SeoEngine:
    """Organisation-scoped facade over Peacock SEO Engine."""

    organisation_id: str
    _engine: PeacockSeoEngine = field(default_factory=PeacockSeoEngine)
    _reports: dict[str, SeoAuditReport] = field(default_factory=dict)

    def status(self) -> dict[str, Any]:
        return {
            "service": "seo_engine",
            "name": "Peacock SEO Engine",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": True,
            "scoring": "deterministic",
            "connectors": ["pagespeed", "core_web_vitals", "search_console", "analytics"],
            "connector_mode": "mock_by_default",
        }

    async def run_audit(
        self,
        crawl: StoredCrawl,
        *,
        fetch_connectors: bool = True,
        interpretation: str | None = None,
    ) -> SeoAuditReport:
        if crawl.organisation_id != self.organisation_id:
            raise PermissionError("Crawl organisation mismatch")
        report = await self._engine.audit_crawl(
            crawl,
            fetch_connectors=fetch_connectors,
            interpretation=interpretation,
        )
        self._reports[report.id] = report
        return report

    def get_report(self, audit_id: str) -> SeoAuditReport | None:
        return self._reports.get(audit_id)
