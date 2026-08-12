"""Crawler ports — Playwright / BeautifulSoup / HTTPX adapters implement these."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class FetchResult:
    url: str
    status_code: int
    html: str
    headers: dict[str, str]


class HttpFetcher(Protocol):
    async def fetch(self, url: str, *, timeout_seconds: float = 30.0) -> FetchResult: ...


class HtmlParser(Protocol):
    def extract_text(self, html: str) -> str: ...

    def extract_title(self, html: str) -> str | None: ...


class BrowserFetcher(Protocol):
    """Playwright-backed fetcher for JS-rendered pages."""

    async def fetch(self, url: str, *, timeout_seconds: float = 60.0) -> FetchResult: ...
