"""Mock connector adapters — safe defaults for local development."""

from __future__ import annotations

from seo_engine.ports import (
    AnalyticsProvider,
    AnalyticsSignal,
    CoreWebVitalsProvider,
    CoreWebVitalsSignal,
    PageSpeedProvider,
    PageSpeedSignal,
    SearchConsoleProvider,
    SearchConsoleSignal,
)


class MockPageSpeedProvider:
    """Returns neutral PageSpeed-like signals without calling Google APIs."""

    def __init__(self, *, performance_score: float = 72.0) -> None:
        self.performance_score = performance_score

    async def fetch(self, url: str) -> PageSpeedSignal:
        return PageSpeedSignal(
            url=url,
            performance_score=self.performance_score,
            accessibility_score=80.0,
            seo_score=85.0,
            source="mock_pagespeed",
            raw={"mock": True, "note": "Replace with live PageSpeed Insights adapter"},
        )


class MockCoreWebVitalsProvider:
    async def fetch(self, url: str) -> CoreWebVitalsSignal:
        return CoreWebVitalsSignal(
            url=url,
            lcp_ms=2200.0,
            cls=0.08,
            inp_ms=160.0,
            ttfb_ms=400.0,
            source="mock_core_web_vitals",
            raw={"mock": True},
        )


class MockSearchConsoleProvider:
    async def fetch(self, site_url: str) -> SearchConsoleSignal:
        return SearchConsoleSignal(
            clicks=0,
            impressions=0,
            ctr=None,
            average_position=None,
            source="mock_search_console",
            raw={"mock": True, "site_url": site_url, "connected": False},
        )


class MockAnalyticsProvider:
    async def fetch(self, property_id: str) -> AnalyticsSignal:
        return AnalyticsSignal(
            sessions=0,
            engaged_sessions=0,
            bounce_rate=None,
            source="mock_analytics",
            raw={"mock": True, "property_id": property_id, "connected": False},
        )


_: PageSpeedProvider = MockPageSpeedProvider()
_: CoreWebVitalsProvider = MockCoreWebVitalsProvider()
_: SearchConsoleProvider = MockSearchConsoleProvider()
_: AnalyticsProvider = MockAnalyticsProvider()
