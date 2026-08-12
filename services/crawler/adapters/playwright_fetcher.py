"""Playwright adapter stub — install browsers in worker images when enabling JS crawl."""

from __future__ import annotations

from crawler.ports import BrowserFetcher, FetchResult


class PlaywrightFetcher:
    async def fetch(self, url: str, *, timeout_seconds: float = 60.0) -> FetchResult:
        raise NotImplementedError(
            "PlaywrightFetcher is scaffolded; enable in worker image when needed"
        )


_: BrowserFetcher = PlaywrightFetcher()
