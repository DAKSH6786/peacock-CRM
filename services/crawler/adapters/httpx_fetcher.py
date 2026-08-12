from __future__ import annotations

import httpx

from crawler.ports import FetchResult, HttpFetcher


class HttpxFetcher:
    """HTTPX adapter for static fetches."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    async def fetch(self, url: str, *, timeout_seconds: float = 30.0) -> FetchResult:
        client = self._client or httpx.AsyncClient(timeout=timeout_seconds)
        owns = self._client is None
        try:
            response = await client.get(url)
            return FetchResult(
                url=str(response.url),
                status_code=response.status_code,
                html=response.text,
                headers={k: v for k, v in response.headers.items()},
            )
        finally:
            if owns:
                await client.aclose()


# Satisfy protocol typing
_: HttpFetcher = HttpxFetcher()  # type: ignore[assignment]
