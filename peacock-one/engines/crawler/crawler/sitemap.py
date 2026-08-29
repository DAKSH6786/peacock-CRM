"""Sitemap discovery and parsing for Peacock Crawler."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import urljoin

from crawler.ports import HttpFetcher
from crawler.url_utils import UrlValidationError, normalise_url


@dataclass(slots=True)
class SitemapDiscovery:
    sitemap_urls: list[str] = field(default_factory=list)
    page_urls: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def parse_sitemap_xml(content: str) -> tuple[list[str], list[str]]:
    """Return ``(page_urls, nested_sitemap_urls)``."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return [], []

    locs: list[str] = []
    for node in root.iter():
        if _local(node.tag) == "loc" and node.text:
            value = node.text.strip()
            if value:
                locs.append(value)
    locs = list(dict.fromkeys(locs))

    root_name = _local(root.tag).lower()
    if root_name == "sitemapindex":
        return [], locs
    if root_name == "urlset":
        return locs, []

    # Ambiguous XML — split by filename hint
    pages: list[str] = []
    nested: list[str] = []
    for loc in locs:
        lower = loc.lower()
        if "sitemap" in lower and lower.endswith(".xml"):
            nested.append(loc)
        else:
            pages.append(loc)
    return pages, nested


async def discover_and_parse_sitemaps(
    seed_url: str,
    fetcher: HttpFetcher,
    *,
    robots_sitemaps: list[str] | None = None,
    timeout_seconds: float = 20.0,
    max_sitemaps: int = 20,
    max_urls: int = 50_000,
) -> SitemapDiscovery:
    normalised = normalise_url(seed_url)
    netloc = normalised.hostname
    if normalised.port:
        netloc = f"{normalised.hostname}:{normalised.port}"
    origin = f"{normalised.scheme}://{netloc}"
    candidates = list(robots_sitemaps or [])
    # Rewrite robots sitemap URLs that dropped an explicit port
    rewritten: list[str] = []
    for sm in candidates:
        try:
            sm_norm = normalise_url(sm)
            if sm_norm.hostname == normalised.hostname and not sm_norm.port and normalised.port:
                rewritten.append(
                    f"{sm_norm.scheme}://{sm_norm.hostname}:{normalised.port}{sm_norm.path}"
                )
            else:
                rewritten.append(sm_norm.normalised)
        except UrlValidationError:
            rewritten.append(sm)
    candidates = rewritten
    candidates.extend(
        [
            urljoin(origin + "/", "sitemap.xml"),
            urljoin(origin + "/", "sitemap_index.xml"),
            urljoin(origin + "/", "sitemap-index.xml"),
        ]
    )
    queue = list(dict.fromkeys(candidates))
    seen_sitemaps: set[str] = set()
    discovery = SitemapDiscovery()

    while queue and len(seen_sitemaps) < max_sitemaps and len(discovery.page_urls) < max_urls:
        sm_url = queue.pop(0)
        if sm_url in seen_sitemaps:
            continue
        seen_sitemaps.add(sm_url)
        discovery.sitemap_urls.append(sm_url)
        try:
            result = await fetcher.fetch(sm_url, timeout_seconds=timeout_seconds)
            if result.error or result.status_code >= 400 or not result.html:
                discovery.errors.append(f"{sm_url} status={result.status_code} error={result.error}")
                continue
            pages, nested = parse_sitemap_xml(result.html)
            for nested_url in nested:
                if nested_url not in seen_sitemaps:
                    queue.append(nested_url)
            for page in pages:
                try:
                    discovery.page_urls.append(normalise_url(page).normalised)
                except UrlValidationError:
                    continue
                if len(discovery.page_urls) >= max_urls:
                    break
        except Exception as exc:  # noqa: BLE001
            discovery.errors.append(f"{sm_url}: {exc}")

    discovery.page_urls = list(dict.fromkeys(discovery.page_urls))
    return discovery
