"""Performance scoring from optional connectors + crawl JS-heavy signals."""

from __future__ import annotations

from typing import Any

from crawler.store import StoredCrawl
from scoring import ScoreResult, clamp, penalty_score
from seo_engine.models import SeoFinding, SeoRecommendation
from seo_engine.ports import CoreWebVitalsSignal, PageSpeedSignal


def analyse_performance(
    crawl: StoredCrawl,
    *,
    pagespeed: PageSpeedSignal | None,
    cwv: CoreWebVitalsSignal | None,
    image_penalties: list[float] | None = None,
) -> tuple[list[SeoFinding], list[SeoRecommendation], ScoreResult, dict[str, Any]]:
    findings: list[SeoFinding] = []
    recs: list[SeoRecommendation] = []
    js_heavy = [p for p in crawl.pages.values() if p.is_js_heavy and (p.status_code or 0) < 400]

    inputs = ["is_js_heavy"]
    positives: list[str] = []
    negatives: list[str] = []
    base = 78.0
    confidence = 0.45  # crawl-only performance is inherently lower confidence
    connector_payload: dict[str, Any] = {}

    if pagespeed and pagespeed.performance_score is not None:
        inputs.extend(["pagespeed.performance_score", f"source={pagespeed.source}"])
        base = float(pagespeed.performance_score)
        confidence = 0.75 if pagespeed.source.startswith("mock") else 0.9
        connector_payload["pagespeed"] = {
            "performance_score": pagespeed.performance_score,
            "source": pagespeed.source,
        }
        if pagespeed.performance_score < 50:
            negatives.append("Low PageSpeed performance score")
            findings.append(
                SeoFinding(
                    code="pagespeed_low",
                    severity="warning",
                    title="Low PageSpeed performance score",
                    description=f"Performance score {pagespeed.performance_score} for {pagespeed.url}.",
                    category="performance",
                    page_urls=[pagespeed.url],
                )
            )
        else:
            positives.append("PageSpeed performance in acceptable range")

    if cwv:
        inputs.extend(["cwv.lcp_ms", "cwv.cls", "cwv.inp_ms", f"source={cwv.source}"])
        connector_payload["core_web_vitals"] = {
            "lcp_ms": cwv.lcp_ms,
            "cls": cwv.cls,
            "inp_ms": cwv.inp_ms,
            "ttfb_ms": cwv.ttfb_ms,
            "source": cwv.source,
        }
        confidence = max(confidence, 0.7 if cwv.source.startswith("mock") else 0.92)
        cwv_penalties = []
        if cwv.lcp_ms is not None and cwv.lcp_ms > 2500:
            cwv_penalties.append(12)
            negatives.append(f"LCP {cwv.lcp_ms}ms exceeds 2.5s")
        if cwv.cls is not None and cwv.cls > 0.1:
            cwv_penalties.append(10)
            negatives.append(f"CLS {cwv.cls} exceeds 0.1")
        if cwv.inp_ms is not None and cwv.inp_ms > 200:
            cwv_penalties.append(8)
            negatives.append(f"INP {cwv.inp_ms}ms exceeds 200ms")
        if cwv_penalties:
            base = penalty_score(base, cwv_penalties)
            findings.append(
                SeoFinding(
                    code="cwv_regressions",
                    severity="warning",
                    title="Core Web Vitals regressions",
                    description="One or more CWV thresholds are not met.",
                    category="performance",
                    page_urls=[cwv.url],
                    evidence=connector_payload["core_web_vitals"],
                )
            )
            recs.append(
                SeoRecommendation(
                    code="improve_cwv",
                    title="Improve Core Web Vitals",
                    priority="high",
                    impact=0.8,
                    effort=0.7,
                    confidence=0.7,
                    affected_pages=[cwv.url],
                    reason="CWV are ranking and UX signals.",
                    suggested_fix="Optimise LCP assets, reduce layout shift, and minimise interaction delay.",
                    category="performance",
                )
            )
        else:
            positives.append("CWV thresholds appear healthy")

    if js_heavy:
        findings.append(
            SeoFinding(
                code="js_heavy_pages",
                severity="opportunity",
                title="JavaScript-heavy pages",
                description=f"{len(js_heavy)} page(s) look JS-heavy from crawl heuristics.",
                category="performance",
                page_urls=[p.url for p in js_heavy[:50]],
            )
        )
        base = penalty_score(base, [min(15.0, 3.0 * len(js_heavy))])
        negatives.append("JS-heavy templates detected")
        recs.append(
            SeoRecommendation(
                code="reduce_js_weight",
                title="Reduce JavaScript weight on key templates",
                priority="medium",
                impact=0.6,
                effort=0.7,
                confidence=0.65,
                affected_pages=[p.url for p in js_heavy[:50]],
                reason="Heavy JS can delay rendering and content discovery.",
                suggested_fix="Ship critical HTML content server-side; defer non-critical scripts.",
                category="performance",
            )
        )

    if image_penalties:
        base = penalty_score(base, image_penalties)
        inputs.append("image_performance_penalties")

    if not pagespeed and not cwv:
        findings.append(
            SeoFinding(
                code="performance_connectors_optional",
                severity="info",
                title="Performance connectors not required",
                description="Audit used crawl heuristics; mock/live PageSpeed & CWV adapters can enrich confidence.",
                category="performance",
            )
        )

    score = ScoreResult(
        code="performance",
        label="Performance",
        score=round(clamp(base, 0.0, 100.0), 2),
        confidence=confidence,
        inputs_used=inputs,
        major_positive_factors=positives[:6],
        major_negative_factors=negatives[:6],
        recommended_actions=[r.title for r in recs[:5]],
    )
    return findings, recs, score, connector_payload
