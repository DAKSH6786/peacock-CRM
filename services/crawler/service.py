"""Peacock Crawler service facade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from crawler.engine import PeacockCrawler
from crawler.policy import CrawlPolicy, POLICY_PRESETS, resolve_policy
from crawler.store import CrawlStore, InMemoryCrawlStore, StoredCrawl


@dataclass(slots=True)
class CrawlerService:
    """Organisation-scoped facade over Peacock Crawler."""

    organisation_id: str
    store: CrawlStore | None = None

    def __post_init__(self) -> None:
        self._store = self.store or InMemoryCrawlStore()
        self._engine = PeacockCrawler(store=self._store)

    @property
    def engine(self) -> PeacockCrawler:
        return self._engine

    def status(self) -> dict[str, Any]:
        return {
            "service": "crawler",
            "name": "Peacock Crawler",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": True,
            "adapters": ["httpx", "beautifulsoup", "playwright"],
            "policy_presets": sorted(POLICY_PRESETS.keys()),
            "controls": ["pause", "resume", "cancel", "restart", "retry_failed"],
        }

    async def ingest_and_crawl(
        self,
        *,
        workspace_id: str,
        url: str,
        policy: CrawlPolicy | None = None,
        policy_preset: str | None = None,
        policy_overrides: dict[str, Any] | None = None,
        max_pages: int | None = None,
        website_id: str | None = None,
        created_by: str | None = None,
    ) -> StoredCrawl:
        resolved = policy or resolve_policy(
            preset=policy_preset,
            overrides=policy_overrides,
            max_pages=max_pages,
        )
        return await self._engine.start(
            organisation_id=self.organisation_id,
            workspace_id=workspace_id,
            seed_url=url,
            policy=resolved,
            website_id=website_id,
            created_by=created_by,
        )
