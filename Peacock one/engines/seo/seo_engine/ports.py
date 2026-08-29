"""Ports for Peacock SEO Engine external connectors.

These connectors are optional for local development. Mock adapters satisfy the
ports so audits run fully offline from crawl data alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True)
class PageSpeedSignal:
    url: str
    performance_score: float | None  # 0–100
    accessibility_score: float | None = None
    seo_score: float | None = None
    source: str = "pagespeed"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CoreWebVitalsSignal:
    url: str
    lcp_ms: float | None
    cls: float | None
    inp_ms: float | None
    ttfb_ms: float | None = None
    source: str = "core_web_vitals"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SearchConsoleSignal:
    clicks: int = 0
    impressions: int = 0
    ctr: float | None = None
    average_position: float | None = None
    source: str = "search_console"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AnalyticsSignal:
    sessions: int = 0
    engaged_sessions: int = 0
    bounce_rate: float | None = None
    source: str = "analytics"
    raw: dict[str, Any] = field(default_factory=dict)


class PageSpeedProvider(Protocol):
    async def fetch(self, url: str) -> PageSpeedSignal: ...


class CoreWebVitalsProvider(Protocol):
    async def fetch(self, url: str) -> CoreWebVitalsSignal: ...


class SearchConsoleProvider(Protocol):
    async def fetch(self, site_url: str) -> SearchConsoleSignal: ...


class AnalyticsProvider(Protocol):
    async def fetch(self, property_id: str) -> AnalyticsSignal: ...


class Clock(Protocol):
    def now_iso(self) -> str: ...
