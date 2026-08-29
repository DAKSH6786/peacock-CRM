"""Peacock SEO Engine API."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_seo import SeoAuditRequest, SeoAuditResponse
from crawler.policy import CrawlPolicy
from crawler.ports import CrawlProgress
from crawler.sqlalchemy_store import SqlAlchemyCrawlStore
from crawler.store import StoredCrawl, StoredPage
from observability.audit import AuditEvent, AuditLogger
from seo_engine import PeacockSeoEngine
from seo_engine.persistence import persist_audit_report

router = APIRouter(prefix="/seo", tags=["peacock-seo-engine"])
audit_logger = AuditLogger()

# Process-local report cache for GET after POST (also persisted when requested)
_REPORTS: dict[str, dict] = {}


def _to_response(payload: dict) -> SeoAuditResponse:
    return SeoAuditResponse(**payload)


def _preview_page(
    *,
    url: str,
    title: str | None,
    meta_description: str | None,
    h1: list[str],
    word_count: int,
    status_code: int = 200,
    internal_links: list[str] | None = None,
    images: list[dict] | None = None,
    schema: list[dict] | None = None,
) -> StoredPage:
    return StoredPage(
        id=str(uuid4()),
        url=url,
        canonical=url,
        status_code=status_code,
        title=title,
        meta_description=meta_description,
        h1=h1,
        h2=[],
        h3=[],
        body_text="Preview body text. " * max(1, word_count // 4),
        word_count=word_count,
        internal_links=internal_links or [],
        external_links=[],
        images=images or [],
        schema=schema or [],
        robots=None,
        indexability="indexable",
        crawl_depth=0,
        content_hash=None,
        content_type="text/html",
        language="en",
        is_js_heavy=False,
        redirect_chain=[],
        fetch_mode="http",
        status="ok",
    )


def _build_preview_crawl(brand: str) -> StoredCrawl:
    home = _preview_page(
        url=f"https://{brand.lower()}.example.com/",
        title=f"{brand} — Generative Visibility Platform",
        meta_description=f"{brand} helps teams win AI and organic search visibility.",
        h1=[f"{brand} — Generative Visibility Platform"],
        word_count=650,
        internal_links=[f"https://{brand.lower()}.example.com/pricing"],
        images=[{"src": "/hero.png", "alt": "Product screenshot"}],
        schema=[{"@type": "Organization"}],
    )
    pricing = _preview_page(
        url=f"https://{brand.lower()}.example.com/pricing",
        title=None,
        meta_description=None,
        h1=[],
        word_count=120,
        images=[{"src": "/plan.png", "alt": None}],
    )
    broken = _preview_page(
        url=f"https://{brand.lower()}.example.com/legacy-page",
        title="Legacy page",
        meta_description="Old page kept for preview purposes.",
        h1=["Legacy page"],
        word_count=80,
        status_code=404,
    )
    pages = {p.url: p for p in (home, pricing, broken)}
    return StoredCrawl(
        id="preview",
        organisation_id="preview",
        workspace_id="preview",
        website_id="preview",
        seed_url=home.url,
        status="completed",
        policy=CrawlPolicy(),
        progress=CrawlProgress(
            pages_discovered=len(pages),
            pages_crawled=2,
            pages_failed=1,
            issues_found=0,
            max_pages=len(pages),
            status="completed",
        ),
        pages=pages,
        robots_raw="User-agent: *\nAllow: /",
        sitemap_urls=[f"https://{brand.lower()}.example.com/sitemap.xml"],
    )


@router.get("/preview", response_model=SeoAuditResponse)
async def seo_audit_preview(brand: str = "Acme") -> SeoAuditResponse:
    """Public demo SEO audit for the Website SEO/AEO/GEO Audit module."""
    crawl = _build_preview_crawl(brand)
    engine = PeacockSeoEngine()
    report = await engine.audit_crawl(crawl, fetch_connectors=False)
    payload = report.to_dict()
    payload["id"] = "preview"
    payload["organisation_id"] = "preview"
    payload["workspace_id"] = "preview"
    payload["title"] = f"{brand} — Peacock SEO preview audit"
    payload["interpretation"] = (
        "Deterministic preview audit generated from example crawl data — "
        "run a real crawl for a client-specific report."
    )
    return _to_response(payload)


@router.post("/audits", response_model=SeoAuditResponse, status_code=201)
async def create_seo_audit(
    body: SeoAuditRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SeoAuditResponse:
    store = SqlAlchemyCrawlStore(db)
    crawl = store.get_crawl(body.crawl_id)
    if crawl is None or crawl.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Crawl not found")

    engine = PeacockSeoEngine()
    report = await engine.audit_crawl(crawl, fetch_connectors=body.fetch_connectors)
    if body.persist:
        if not report.website_id:
            raise HTTPException(status_code=400, detail="Crawl has no website_id; cannot persist audit")
        persist_audit_report(db, report)

    payload = report.to_dict()
    _REPORTS[report.id] = payload

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="seo.audit.create",
            resource_type="audit",
            resource_id=report.id,
            workspace_id=crawl.workspace_id,
            metadata={
                "crawl_id": crawl.id,
                "peacock_seo_score": report.peacock_seo_score.score,
            },
        )
    )
    return _to_response(payload)


@router.get("/audits/{audit_id}", response_model=SeoAuditResponse)
def get_seo_audit(
    audit_id: str,
    ctx: AuthContext = Depends(get_auth_context),
) -> SeoAuditResponse:
    payload = _REPORTS.get(audit_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Audit not found in session cache")
    if payload.get("organisation_id") != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Audit not found")
    return _to_response(payload)


@router.get("/audits/{audit_id}/overview", response_model=SeoAuditResponse)
def get_seo_audit_overview(
    audit_id: str,
    ctx: AuthContext = Depends(get_auth_context),
) -> SeoAuditResponse:
    return get_seo_audit(audit_id, ctx)
