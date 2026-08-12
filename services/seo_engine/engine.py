"""Peacock SEO Engine — deterministic crawl → audit transformation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import uuid4

from crawler.store import StoredCrawl
from scoring import ScoreResult, peacock_seo_score, weighted_score
from seo_engine.adapters import (
    MockAnalyticsProvider,
    MockCoreWebVitalsProvider,
    MockPageSpeedProvider,
    MockSearchConsoleProvider,
)
from seo_engine.analyzers import (
    analyse_content,
    analyse_crawlability,
    analyse_images,
    analyse_linking,
    analyse_metadata,
    analyse_performance,
    analyse_structured_data,
)
from seo_engine.models import PageIssueSummary, SeoAuditReport, SeoRecommendation
from seo_engine.ports import (
    AnalyticsProvider,
    CoreWebVitalsProvider,
    PageSpeedProvider,
    SearchConsoleProvider,
)


class PeacockSeoEngine:
    """Transforms crawl data into an actionable, explainable SEO audit."""

    name = "Peacock SEO Engine"

    def __init__(
        self,
        *,
        pagespeed: PageSpeedProvider | None = None,
        cwv: CoreWebVitalsProvider | None = None,
        search_console: SearchConsoleProvider | None = None,
        analytics: AnalyticsProvider | None = None,
        use_mock_connectors: bool = True,
    ) -> None:
        if use_mock_connectors:
            self.pagespeed = pagespeed or MockPageSpeedProvider()
            self.cwv = cwv or MockCoreWebVitalsProvider()
            self.search_console = search_console or MockSearchConsoleProvider()
            self.analytics = analytics or MockAnalyticsProvider()
        else:
            self.pagespeed = pagespeed
            self.cwv = cwv
            self.search_console = search_console
            self.analytics = analytics

    async def audit_crawl(
        self,
        crawl: StoredCrawl,
        *,
        fetch_connectors: bool = True,
        interpretation: str | None = None,
    ) -> SeoAuditReport:
        findings = []
        recommendations: list[SeoRecommendation] = []
        scores: dict[str, ScoreResult] = {}

        f1, r1, technical, indexability = analyse_crawlability(crawl)
        findings.extend(f1)
        recommendations.extend(r1)
        scores["technical_seo"] = technical
        scores["indexability"] = indexability

        f2, r2, on_page = analyse_metadata(crawl)
        findings.extend(f2)
        recommendations.extend(r2)

        f3, r3, content = analyse_content(crawl)
        findings.extend(f3)
        recommendations.extend(r3)
        scores["content_quality"] = content

        f4, r4, linking = analyse_linking(crawl)
        findings.extend(f4)
        recommendations.extend(r4)
        scores["internal_linking"] = linking

        f5, r5, image_penalties = analyse_images(crawl)
        findings.extend(f5)
        recommendations.extend(r5)
        # Fold image penalties into on-page score deterministically
        on_page.score = max(0.0, round(on_page.score - sum(image_penalties), 2))
        if image_penalties:
            on_page.inputs_used.append("image_penalties")
            on_page.major_negative_factors.extend(
                [f.title for f in f5 if f.severity in {"critical", "warning"}][:3]
            )
        scores["on_page_seo"] = on_page

        f6, r6, structured = analyse_structured_data(crawl)
        findings.extend(f6)
        recommendations.extend(r6)
        scores["structured_data"] = structured

        pagespeed_signal = None
        cwv_signal = None
        gsc_signal = None
        analytics_signal = None
        if fetch_connectors:
            seed = crawl.seed_url
            if self.pagespeed is not None:
                pagespeed_signal = await self.pagespeed.fetch(seed)
            if self.cwv is not None:
                cwv_signal = await self.cwv.fetch(seed)
            if self.search_console is not None:
                gsc_signal = await self.search_console.fetch(seed)
            if self.analytics is not None:
                analytics_signal = await self.analytics.fetch(crawl.website_id or seed)

        f7, r7, performance, connector_payload = analyse_performance(
            crawl,
            pagespeed=pagespeed_signal,
            cwv=cwv_signal,
            image_penalties=[p for p in image_penalties if p],
        )
        findings.extend(f7)
        recommendations.extend(r7)
        scores["performance"] = performance

        if gsc_signal is not None:
            connector_payload["search_console"] = {
                "clicks": gsc_signal.clicks,
                "impressions": gsc_signal.impressions,
                "ctr": gsc_signal.ctr,
                "average_position": gsc_signal.average_position,
                "source": gsc_signal.source,
                "raw": gsc_signal.raw,
            }
        if analytics_signal is not None:
            connector_payload["analytics"] = {
                "sessions": analytics_signal.sessions,
                "engaged_sessions": analytics_signal.engaged_sessions,
                "bounce_rate": analytics_signal.bounce_rate,
                "source": analytics_signal.source,
                "raw": analytics_signal.raw,
            }

        # Priority scores for recommendations (deterministic)
        for rec in recommendations:
            rec.priority_score = round(
                weighted_score(rec.impact, rec.confidence, rec.effort),
                4,
            )
        recommendations.sort(key=lambda r: (-r.priority_score, r.title))

        # Deduplicate findings by code+title while merging page urls
        merged: dict[str, Any] = {}
        for finding in findings:
            key = f"{finding.code}:{finding.title}"
            if key not in merged:
                merged[key] = finding
            else:
                existing = merged[key]
                existing.page_urls = list(dict.fromkeys(existing.page_urls + finding.page_urls))[:50]
        findings = list(merged.values())
        severity_rank = {"critical": 0, "warning": 1, "opportunity": 2, "info": 3}
        findings.sort(key=lambda f: (severity_rank.get(f.severity, 9), f.title))

        page_map: dict[str, list[str]] = defaultdict(list)
        page_sev: dict[str, list[str]] = defaultdict(list)
        for finding in findings:
            if finding.severity == "info":
                continue
            for url in finding.page_urls:
                page_map[url].append(finding.title)
                page_sev[url].append(finding.severity)
        page_issues = [
            PageIssueSummary(url=url, issues=issues, severities=page_sev[url])
            for url, issues in sorted(page_map.items())
        ]

        overall = peacock_seo_score(scores)
        critical_n = sum(1 for f in findings if f.severity == "critical")
        warning_n = sum(1 for f in findings if f.severity == "warning")
        opportunity_n = sum(1 for f in findings if f.severity == "opportunity")
        summary = (
            f"Peacock SEO Score {overall.score}/100 (confidence {overall.confidence}). "
            f"{critical_n} critical, {warning_n} warnings, {opportunity_n} opportunities across "
            f"{len(crawl.pages)} crawled page(s)."
        )

        # Optional narrative — never used as the numeric score input
        if interpretation is None:
            interpretation = (
                "Scores are computed deterministically from crawl metrics and optional connector "
                "signals. Use recommendations ordered by priority_score (impact × confidence × effort)."
            )

        return SeoAuditReport(
            id=str(uuid4()),
            organisation_id=crawl.organisation_id,
            workspace_id=crawl.workspace_id,
            website_id=crawl.website_id,
            crawl_id=crawl.id,
            status="completed",
            title=f"SEO audit for {crawl.seed_url}",
            summary=summary,
            peacock_seo_score=overall,
            scores=scores,
            findings=findings,
            recommendations=recommendations,
            page_issues=page_issues,
            connector_signals=connector_payload,
            interpretation=interpretation,
        )
