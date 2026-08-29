"""Crawler ports — HTTPX / BeautifulSoup / Playwright adapters implement these."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class FetchResult:
    url: str
    status_code: int
    html: str
    headers: dict[str, str]
    redirect_chain: list[str] = field(default_factory=list)
    error: str | None = None


class HttpFetcher(Protocol):
    async def fetch(self, url: str, *, timeout_seconds: float = 30.0) -> FetchResult: ...


class HtmlParser(Protocol):
    def extract_text(self, html: str) -> str: ...

    def extract_title(self, html: str) -> str | None: ...


class BrowserFetcher(Protocol):
    """Playwright-backed fetcher for JS-rendered pages."""

    async def fetch(self, url: str, *, timeout_seconds: float = 60.0) -> FetchResult: ...

    @property
    def available(self) -> bool: ...


@dataclass(slots=True)
class CrawlProgress:
    pages_discovered: int = 0
    pages_crawled: int = 0
    pages_failed: int = 0
    issues_found: int = 0
    max_pages: int = 0
    status: str = "pending"

    @property
    def progress_percent(self) -> float:
        denominator = max(self.max_pages, self.pages_discovered, 1)
        completed = self.pages_crawled + self.pages_failed
        return round(min(100.0, (completed / denominator) * 100.0), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pages_discovered": self.pages_discovered,
            "pages_crawled": self.pages_crawled,
            "pages_failed": self.pages_failed,
            "issues_found": self.issues_found,
            "progress_percent": self.progress_percent,
            "max_pages": self.max_pages,
            "status": self.status,
        }
