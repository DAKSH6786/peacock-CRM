"""Playwright adapter for JS-rendered pages."""

from __future__ import annotations

from crawler.ports import BrowserFetcher, FetchResult


class PlaywrightFetcher:
    """Optional browser fetcher. ``available`` is False when Playwright/browsers missing."""

    def __init__(self, *, user_agent: str = "PeacockCrawler/1.0") -> None:
        self._user_agent = user_agent
        self._available: bool | None = None

    @property
    def available(self) -> bool:
        if self._available is None:
            try:
                from playwright.async_api import async_playwright  # noqa: F401

                self._available = True
            except Exception:  # noqa: BLE001
                self._available = False
        return bool(self._available)

    async def fetch(self, url: str, *, timeout_seconds: float = 60.0) -> FetchResult:
        if not self.available:
            return FetchResult(
                url=url,
                status_code=0,
                html="",
                headers={},
                redirect_chain=[url],
                error="Playwright is not available in this environment",
            )
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=self._user_agent)
                page = await context.new_page()
                response = await page.goto(url, wait_until="networkidle", timeout=int(timeout_seconds * 1000))
                html = await page.content()
                final_url = page.url
                status = response.status if response else 0
                headers = await response.all_headers() if response else {}
                await context.close()
                await browser.close()
                return FetchResult(
                    url=final_url,
                    status_code=status,
                    html=html,
                    headers={k: v for k, v in headers.items()},
                    redirect_chain=[url, final_url] if final_url != url else [final_url],
                )
        except Exception as exc:  # noqa: BLE001
            return FetchResult(
                url=url,
                status_code=0,
                html="",
                headers={},
                redirect_chain=[url],
                error=str(exc),
            )


_: BrowserFetcher = PlaywrightFetcher()
