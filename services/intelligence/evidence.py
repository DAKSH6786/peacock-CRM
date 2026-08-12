"""Deterministic evidence collectors — quantitative facts before LLM reasoning."""

from __future__ import annotations

from intelligence.models import EvidenceBundle, EvidenceItem, EvidenceKind, PipelineState
from intelligence.ports import EvidenceCollector


class CrawlEvidenceCollector:
    code = "crawl_findings"

    def collect(self, state: PipelineState) -> list[EvidenceItem]:
        meta = state.request.metadata or {}
        crawl = meta.get("crawl") or {}
        if not crawl and not state.request.crawl_id:
            return []
        items: list[EvidenceItem] = []
        pages_crawled = int(crawl.get("pages_crawled") or meta.get("pages_crawled") or 0)
        pages_failed = int(crawl.get("pages_failed") or meta.get("pages_failed") or 0)
        issues = int(crawl.get("issues_found") or meta.get("issues_found") or 0)
        if pages_crawled or state.request.crawl_id:
            items.append(
                EvidenceItem(
                    code="crawl.pages_crawled",
                    label="Pages crawled",
                    value=pages_crawled,
                    kind=EvidenceKind.DETERMINISTIC,
                    source="crawler",
                    confidence=0.95 if pages_crawled else 0.4,
                    unit="count",
                    metadata={"crawl_id": state.request.crawl_id},
                )
            )
            items.append(
                EvidenceItem(
                    code="crawl.pages_failed",
                    label="Pages failed",
                    value=pages_failed,
                    kind=EvidenceKind.DETERMINISTIC,
                    source="crawler",
                    confidence=0.95,
                    unit="count",
                )
            )
            items.append(
                EvidenceItem(
                    code="crawl.issues_found",
                    label="Crawl issues found",
                    value=issues,
                    kind=EvidenceKind.DETERMINISTIC,
                    source="crawler",
                    confidence=0.9,
                    unit="count",
                )
            )
        for finding in meta.get("crawl_findings") or []:
            items.append(
                EvidenceItem(
                    code=f"crawl.finding.{finding.get('code', 'unknown')}",
                    label=str(finding.get("title") or finding.get("code")),
                    value=finding.get("count", 1),
                    kind=EvidenceKind.DETERMINISTIC,
                    source="crawler",
                    confidence=0.9,
                    related_urls=list(finding.get("page_urls") or [])[:20],
                    metadata=finding,
                )
            )
        return items


class SeoAuditEvidenceCollector:
    code = "seo_audit"

    def collect(self, state: PipelineState) -> list[EvidenceItem]:
        meta = state.request.metadata or {}
        audit = meta.get("seo_audit") or {}
        if not audit and not state.request.audit_id:
            return []
        items: list[EvidenceItem] = []
        score = audit.get("peacock_seo_score")
        if score is not None:
            items.append(
                EvidenceItem(
                    code="seo.peacock_score",
                    label="Peacock SEO Score",
                    value=float(score),
                    kind=EvidenceKind.DETERMINISTIC,
                    source="seo_engine",
                    confidence=0.95,
                    unit="score_0_100",
                    metadata={"audit_id": state.request.audit_id},
                )
            )
        for section, value in (audit.get("section_scores") or {}).items():
            items.append(
                EvidenceItem(
                    code=f"seo.section.{section}",
                    label=f"SEO section score: {section}",
                    value=float(value),
                    kind=EvidenceKind.DETERMINISTIC,
                    source="seo_engine",
                    confidence=0.9,
                    unit="score_0_100",
                )
            )
        for key in ("critical_issues", "warnings", "opportunities"):
            if key in audit:
                items.append(
                    EvidenceItem(
                        code=f"seo.{key}",
                        label=key.replace("_", " ").title(),
                        value=int(audit[key]),
                        kind=EvidenceKind.DETERMINISTIC,
                        source="seo_engine",
                        confidence=0.9,
                        unit="count",
                    )
                )
        return items


class PerformanceEvidenceCollector:
    code = "page_performance"

    def collect(self, state: PipelineState) -> list[EvidenceItem]:
        perf = (state.request.metadata or {}).get("performance") or {}
        items: list[EvidenceItem] = []
        for key, label in [
            ("lcp_ms", "LCP (ms)"),
            ("cls", "CLS"),
            ("inp_ms", "INP (ms)"),
            ("pagespeed_score", "PageSpeed score"),
        ]:
            if key in perf and perf[key] is not None:
                items.append(
                    EvidenceItem(
                        code=f"perf.{key}",
                        label=label,
                        value=perf[key],
                        kind=EvidenceKind.DETERMINISTIC,
                        source="performance_connectors",
                        confidence=0.7,
                    )
                )
        return items


class VisibilityEvidenceCollector:
    code = "visibility_signals"

    def collect(self, state: PipelineState) -> list[EvidenceItem]:
        vis = (state.request.metadata or {}).get("visibility") or {}
        items: list[EvidenceItem] = []
        mapping = {
            "brand_mentions": "Brand mentions",
            "citation_counts": "Citation counts",
            "prompt_results": "AI prompt result hits",
            "backlinks": "Backlinks",
            "rankings_top10": "Keywords in top 10",
            "traffic": "Organic traffic",
            "keyword_overlap": "Keyword overlap vs competitors",
            "content_overlap": "Content overlap score",
            "internal_links_avg": "Avg internal links / page",
            "content_freshness_days": "Median content age (days)",
        }
        for key, label in mapping.items():
            if key in vis and vis[key] is not None:
                items.append(
                    EvidenceItem(
                        code=f"vis.{key}",
                        label=label,
                        value=vis[key],
                        kind=EvidenceKind.DETERMINISTIC,
                        source="visibility_metrics",
                        confidence=0.8,
                    )
                )
        return items


class HistoricalPerformanceCollector:
    code = "historical_performance"

    def collect(self, state: PipelineState) -> list[EvidenceItem]:
        hist = (state.request.metadata or {}).get("historical_performance") or {}
        items: list[EvidenceItem] = []
        for key, value in hist.items():
            items.append(
                EvidenceItem(
                    code=f"hist.{key}",
                    label=f"Historical: {key}",
                    value=value,
                    kind=EvidenceKind.DETERMINISTIC,
                    source="monitoring",
                    confidence=0.75,
                )
            )
        return items


DEFAULT_COLLECTORS: list[EvidenceCollector] = [
    CrawlEvidenceCollector(),
    SeoAuditEvidenceCollector(),
    PerformanceEvidenceCollector(),
    VisibilityEvidenceCollector(),
    HistoricalPerformanceCollector(),
]


def collect_deterministic_evidence(
    state: PipelineState,
    collectors: list[EvidenceCollector] | None = None,
) -> EvidenceBundle:
    bundle = EvidenceBundle()
    for collector in collectors or DEFAULT_COLLECTORS:
        # Honour required_data / intent — skip irrelevant collectors when possible
        required = set(state.classification.required_data if state.classification else [])
        if required:
            relevance_hints = {
                "crawl_findings": {"crawl_summary", "seo_audit_summary", "website_architecture"},
                "seo_audit": {"seo_audit_summary", "crawl_summary"},
                "page_performance": {"website_architecture", "seo_audit_summary"},
                "visibility_signals": {"competitors", "brand", "historical_performance"},
                "historical_performance": {"historical_performance", "conversion_objectives"},
            }
            hints = relevance_hints.get(collector.code, set())
            if hints and not (hints & required) and collector.code not in required:
                # Still collect if metadata explicitly provides the payload
                meta = state.request.metadata or {}
                has_payload = any(
                    key in meta
                    for key in ("crawl", "seo_audit", "performance", "visibility", "historical_performance")
                )
                if not has_payload:
                    continue
        for item in collector.collect(state):
            if item.kind != EvidenceKind.DETERMINISTIC:
                # Hard separation — collectors must not emit LLM inference here
                continue
            bundle.deterministic.append(item)
    return bundle
