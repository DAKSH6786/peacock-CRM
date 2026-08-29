"""robots.txt inspection for Peacock Crawler."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

from crawler.ports import FetchResult, HttpFetcher
from crawler.url_utils import normalise_url


@dataclass(slots=True)
class RobotsInspection:
    robots_url: str
    fetched: bool
    status_code: int | None
    can_fetch_seed: bool
    sitemap_urls: list[str] = field(default_factory=list)
    raw_text: str | None = None
    error: str | None = None


async def inspect_robots(
    seed_url: str,
    fetcher: HttpFetcher,
    *,
    user_agent: str,
    timeout_seconds: float = 15.0,
) -> RobotsInspection:
    normalised = normalise_url(seed_url)
    netloc = normalised.hostname
    if normalised.port:
        netloc = f"{normalised.hostname}:{normalised.port}"
    robots_url = urljoin(f"{normalised.scheme}://{netloc}/", "robots.txt")
    try:
        result: FetchResult = await fetcher.fetch(robots_url, timeout_seconds=timeout_seconds)
    except Exception as exc:  # noqa: BLE001 — never crash workers on robots failures
        return RobotsInspection(
            robots_url=robots_url,
            fetched=False,
            status_code=None,
            can_fetch_seed=True,
            error=str(exc),
        )

    if result.status_code >= 400:
        return RobotsInspection(
            robots_url=robots_url,
            fetched=False,
            status_code=result.status_code,
            can_fetch_seed=True,
            raw_text=result.html[:50_000] if result.html else None,
        )

    parser = RobotFileParser()
    parser.parse(result.html.splitlines())
    sitemaps: list[str] = []
    for line in result.html.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("sitemap:"):
            candidate = stripped.split(":", 1)[1].strip()
            if candidate:
                # Preserve seed port when robots authors omit it
                if normalised.port and "://" in candidate:
                    from crawler.url_utils import UrlValidationError, normalise_url as _nu

                    try:
                        sm = _nu(candidate)
                        if sm.hostname == normalised.hostname and not sm.port:
                            candidate = f"{sm.scheme}://{sm.hostname}:{normalised.port}{sm.path}"
                    except UrlValidationError:
                        pass
                sitemaps.append(candidate)

    can_fetch = True
    try:
        can_fetch = bool(parser.can_fetch(user_agent, normalised.normalised))
    except Exception:  # noqa: BLE001
        can_fetch = True

    return RobotsInspection(
        robots_url=robots_url,
        fetched=True,
        status_code=result.status_code,
        can_fetch_seed=can_fetch,
        sitemap_urls=sitemaps,
        raw_text=result.html[:50_000],
    )


def is_allowed(robots: RobotsInspection | None, url: str, *, user_agent: str, respect: bool) -> bool:
    if not respect or robots is None or not robots.fetched or not robots.raw_text:
        return True
    parser = RobotFileParser()
    parser.parse(robots.raw_text.splitlines())
    try:
        return bool(parser.can_fetch(user_agent, url))
    except Exception:  # noqa: BLE001
        return True
