"""Configurable crawl policies for Peacock Crawler.

Commercial plan limits (Free trial / Starter / Pro / Enterprise) MUST NOT be
hardcoded in the crawler engine. Map plans to ``CrawlPolicy`` at the API or
billing boundary, then pass the policy object into the crawler.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Mapping


@dataclass(slots=True)
class CrawlPolicy:
    """Operational limits and behaviour for a single crawl run."""

    max_pages: int = 100
    max_depth: int = 5
    respect_robots: bool = True
    same_host_only: bool = True
    fetch_timeout_seconds: float = 20.0
    render_timeout_seconds: float = 45.0
    concurrency: int = 4
    max_retries_per_url: int = 2
    retry_backoff_seconds: float = 0.5
    user_agent: str = "PeacockCrawler/1.0 (+https://peacock.one/bot)"
    allow_js_render: bool = True
    force_js_render: bool = False
    js_heavy_script_threshold: int = 8
    js_heavy_body_char_threshold: int = 120
    require_dns: bool = False
    # When False (default), reject localhost/private/metadata hosts and private DNS (SSRF).
    # Local integration tests may set True for loopback mock servers only.
    allow_private_hosts: bool = False
    follow_redirects: bool = True
    max_redirects: int = 8
    discover_sitemaps: bool = True
    parse_sitemaps: bool = True
    near_duplicate_threshold: float = 0.92
    store_body_text: bool = True
    max_body_chars: int = 200_000
    allowed_schemes: tuple[str, ...] = ("http", "https")

    def __post_init__(self) -> None:
        if self.max_pages < 1:
            raise ValueError("max_pages must be >= 1")
        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if self.concurrency < 1:
            raise ValueError("concurrency must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> CrawlPolicy:
        if not data:
            return cls()
        allowed = {f.name for f in fields(cls)}
        kwargs = {k: v for k, v in data.items() if k in allowed}
        # tuples may arrive as lists from JSON
        if "allowed_schemes" in kwargs and isinstance(kwargs["allowed_schemes"], list):
            kwargs["allowed_schemes"] = tuple(kwargs["allowed_schemes"])
        return cls(**kwargs)


# Named presets for product/billing layers — NOT imported by the crawl engine.
POLICY_PRESETS: dict[str, CrawlPolicy] = {
    "free_trial": CrawlPolicy(max_pages=100, max_depth=3),
    "starter": CrawlPolicy(max_pages=1_000, max_depth=5),
    "pro": CrawlPolicy(max_pages=10_000, max_depth=8, concurrency=8),
    "enterprise": CrawlPolicy(max_pages=50_000, max_depth=12, concurrency=12),
}


def resolve_policy(
    *,
    preset: str | None = None,
    overrides: Mapping[str, Any] | None = None,
    max_pages: int | None = None,
) -> CrawlPolicy:
    """Build a policy from an optional preset name + overrides.

    Enterprise / custom limits: pass ``max_pages`` or a full override mapping.
    """
    base = POLICY_PRESETS[preset].to_dict() if preset and preset in POLICY_PRESETS else CrawlPolicy().to_dict()
    if overrides:
        base.update(dict(overrides))
    if max_pages is not None:
        base["max_pages"] = max_pages
    return CrawlPolicy.from_mapping(base)
