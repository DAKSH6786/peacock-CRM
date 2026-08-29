"""HTTPX adapter for Peacock Crawler with redirect-chain capture."""

from __future__ import annotations

import httpx

from crawler.ports import FetchResult, HttpFetcher


class HttpxFetcher:
    """HTTPX adapter for static fetches. Never raises to the engine — errors become FetchResult."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        user_agent: str = "PeacockCrawler/1.0",
        follow_redirects: bool = True,
        max_redirects: int = 8,
    ) -> None:
        self._client = client
        self._user_agent = user_agent
        self._follow_redirects = follow_redirects
        self._max_redirects = max_redirects

    async def fetch(self, url: str, *, timeout_seconds: float = 30.0) -> FetchResult:
        headers = {"User-Agent": self._user_agent, "Accept": "text/html,application/xhtml+xml,*/*"}
        client = self._client or httpx.AsyncClient(
            timeout=timeout_seconds,
            follow_redirects=self._follow_redirects,
            max_redirects=self._max_redirects,
            headers=headers,
        )
        owns = self._client is None
        try:
            response = await client.get(url)
            chain = [str(item.url) for item in response.history] + [str(response.url)]
            return FetchResult(
                url=str(response.url),
                status_code=response.status_code,
                html=response.text,
                headers={k: v for k, v in response.headers.items()},
                redirect_chain=chain,
            )
        except Exception as exc:  # noqa: BLE001 — isolate malformed sites / network faults
            return FetchResult(
                url=url,
                status_code=0,
                html="",
                headers={},
                redirect_chain=[url],
                error=str(exc),
            )
        finally:
            if owns:
                await client.aclose()


_: HttpFetcher = HttpxFetcher()  # type: ignore[assignment]
