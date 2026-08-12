"""Website ingestion and Peacock Crawler control API."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db import SessionLocal, get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_crawler import (
    CrawlProgressResponse,
    CrawlResponse,
    CrawlStartRequest,
    WebsiteIngestRequest,
    WebsiteResponse,
)
from api.worker import get_job_runner
from crawler.engine import PeacockCrawler
from crawler.policy import resolve_policy
from crawler.sqlalchemy_store import SqlAlchemyCrawlStore, ensure_website_for_url
from crawler.store import StoredCrawl
from crawler.url_utils import UrlValidationError, normalise_url
from db_models import BackgroundJob, Crawl, Website
from job_runtime import JobSubmission
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(tags=["peacock-crawler"])
audit = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _serialize_crawl(crawl: StoredCrawl, *, include_pages: bool = True) -> CrawlResponse:
    pages = []
    issues = []
    if include_pages:
        for page in crawl.pages.values():
            pages.append(
                {
                    "id": page.id,
                    "url": page.url,
                    "canonical": page.canonical,
                    "status_code": page.status_code,
                    "title": page.title,
                    "meta_description": page.meta_description,
                    "h1": page.h1,
                    "h2": page.h2,
                    "h3": page.h3,
                    "body_text": page.body_text,
                    "word_count": page.word_count,
                    "internal_links": page.internal_links,
                    "external_links": page.external_links,
                    "images": page.images,
                    "schema_blocks": page.schema,
                    "robots": page.robots,
                    "indexability": page.indexability,
                    "crawl_depth": page.crawl_depth,
                    "content_hash": page.content_hash,
                    "content_type": page.content_type,
                    "language": page.language,
                    "status": page.status,
                    "is_js_heavy": page.is_js_heavy,
                    "is_near_duplicate": page.is_near_duplicate,
                    "is_orphan_candidate": page.is_orphan_candidate,
                }
            )
        issues = [
            {
                "id": issue.id,
                "code": issue.code,
                "severity": issue.severity,
                "message": issue.message,
                "page_url": issue.page_url,
                "status": issue.status,
            }
            for issue in crawl.issues
        ]
    return CrawlResponse(
        id=crawl.id,
        website_id=crawl.website_id,
        seed_url=crawl.seed_url,
        status=crawl.status,
        organisation_id=crawl.organisation_id,
        workspace_id=crawl.workspace_id,
        progress=CrawlProgressResponse(**crawl.progress.to_dict()),
        policy=crawl.policy.to_dict(),
        error_summary=crawl.error_summary,
        pages=pages,
        issues=issues,
    )


@router.post("/websites", response_model=WebsiteResponse, status_code=201)
def ingest_website(
    body: WebsiteIngestRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> WebsiteResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    try:
        normalised = normalise_url(body.url)
    except UrlValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    website = ensure_website_for_url(
        db,
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
        url=normalised.normalised,
        created_by=ctx.user.id,
    )
    if body.name:
        website.name = body.name
        db.commit()

    audit.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="websites.ingest",
            resource_type="website",
            resource_id=website.id,
            workspace_id=workspace_id,
            metadata={"domain": website.primary_domain},
        )
    )
    return WebsiteResponse(
        id=website.id,
        name=website.name,
        primary_domain=website.primary_domain,
        root_url=website.root_url,
        workspace_id=website.workspace_id,
        organisation_id=website.organisation_id,
        status=website.status,
    )


@router.get("/websites", response_model=list[WebsiteResponse])
def list_websites(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[WebsiteResponse]:
    rows = db.scalars(
        select(Website).where(Website.organisation_id == ctx.organisation.id).order_by(Website.created_at.desc())
    ).all()
    return [
        WebsiteResponse(
            id=row.id,
            name=row.name,
            primary_domain=row.primary_domain,
            root_url=row.root_url,
            workspace_id=row.workspace_id,
            organisation_id=row.organisation_id,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/crawls", response_model=CrawlResponse, status_code=202)
async def start_crawl(
    body: CrawlStartRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CrawlResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    seed = body.url
    website_id = body.website_id
    if website_id:
        website = db.get(Website, website_id)
        if not website or website.organisation_id != ctx.organisation.id:
            raise HTTPException(status_code=404, detail="Website not found")
        seed = seed or website.root_url
    if not seed:
        raise HTTPException(status_code=400, detail="url or website_id is required")

    try:
        normalised = normalise_url(seed)
    except UrlValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    website = ensure_website_for_url(
        db,
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
        url=normalised.normalised,
        created_by=ctx.user.id,
    )
    policy = resolve_policy(
        preset=body.policy_preset,
        overrides=body.policy,
        max_pages=body.max_pages,
    )

    store = SqlAlchemyCrawlStore(db)
    engine = PeacockCrawler(store=store)

    if body.run_inline:
        crawl = await engine.start(
            organisation_id=ctx.organisation.id,
            workspace_id=workspace_id,
            seed_url=normalised.normalised,
            policy=policy,
            website_id=website.id,
            created_by=ctx.user.id,
        )
    else:
        crawl = store.create_crawl(
            organisation_id=ctx.organisation.id,
            workspace_id=workspace_id,
            seed_url=normalised.normalised,
            policy=policy,
            website_id=website.id,
            created_by=ctx.user.id,
        )
        runner = get_job_runner()
        submission = JobSubmission(
            name="peacock.crawl",
            organisation_id=ctx.organisation.id,
            workspace_id=workspace_id,
            payload={"crawl_id": crawl.id},
        )
        handle = runner.enqueue(submission)
        row = db.get(Crawl, crawl.id)
        if row:
            row.job_id = handle.id
            row.status = "queued"
            db.add(
                BackgroundJob(
                    id=handle.id,
                    organisation_id=ctx.organisation.id,
                    workspace_id=workspace_id,
                    name=handle.name,
                    status=handle.status.value,
                    backend=handle.backend,
                    payload=submission.payload,
                )
            )
            db.commit()
        crawl = store.get_crawl(crawl.id) or crawl

    audit.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="crawls.start",
            resource_type="crawl",
            resource_id=crawl.id,
            workspace_id=workspace_id,
            metadata={"seed_url": normalised.normalised, "max_pages": policy.max_pages},
        )
    )
    return _serialize_crawl(crawl)


@router.get("/crawls/{crawl_id}", response_model=CrawlResponse)
def get_crawl(
    crawl_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CrawlResponse:
    store = SqlAlchemyCrawlStore(db)
    crawl = store.get_crawl(crawl_id)
    if crawl is None or crawl.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Crawl not found")
    return _serialize_crawl(crawl)


@router.get("/crawls/{crawl_id}/progress", response_model=CrawlProgressResponse)
def get_crawl_progress(
    crawl_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CrawlProgressResponse:
    store = SqlAlchemyCrawlStore(db)
    crawl = store.get_crawl(crawl_id)
    if crawl is None or crawl.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Crawl not found")
    return CrawlProgressResponse(**crawl.progress.to_dict())


def _control(crawl_id: str, ctx: AuthContext, db: Session, action: str) -> CrawlResponse:
    store = SqlAlchemyCrawlStore(db)
    crawl = store.get_crawl(crawl_id)
    if crawl is None or crawl.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Crawl not found")
    engine = PeacockCrawler(store=store)
    if action == "pause":
        crawl = engine.pause(crawl_id)
    elif action == "resume":
        crawl = engine.resume(crawl_id)
    elif action == "cancel":
        crawl = engine.cancel(crawl_id)
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    return _serialize_crawl(crawl, include_pages=False)


@router.post("/crawls/{crawl_id}/pause", response_model=CrawlResponse)
def pause_crawl(
    crawl_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CrawlResponse:
    return _control(crawl_id, ctx, db, "pause")


@router.post("/crawls/{crawl_id}/resume", response_model=CrawlResponse)
def resume_crawl(
    crawl_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CrawlResponse:
    return _control(crawl_id, ctx, db, "resume")


@router.post("/crawls/{crawl_id}/cancel", response_model=CrawlResponse)
def cancel_crawl(
    crawl_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CrawlResponse:
    return _control(crawl_id, ctx, db, "cancel")


@router.post("/crawls/{crawl_id}/restart", response_model=CrawlResponse)
async def restart_crawl(
    crawl_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CrawlResponse:
    store = SqlAlchemyCrawlStore(db)
    previous = store.get_crawl(crawl_id)
    if previous is None or previous.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Crawl not found")
    engine = PeacockCrawler(store=store)
    crawl = await engine.restart(
        crawl_id,
        organisation_id=ctx.organisation.id,
        workspace_id=previous.workspace_id,
    )
    return _serialize_crawl(crawl)


@router.post("/crawls/{crawl_id}/retry-failed", response_model=CrawlResponse)
async def retry_failed_urls(
    crawl_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CrawlResponse:
    store = SqlAlchemyCrawlStore(db)
    crawl = store.get_crawl(crawl_id)
    if crawl is None or crawl.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Crawl not found")
    engine = PeacockCrawler(store=store)
    crawl = await engine.retry_failed(crawl_id)
    return _serialize_crawl(crawl)


def run_crawl_job(crawl_id: str) -> dict[str, Any]:
    """Sync entrypoint for Celery / memory job runners."""
    db = SessionLocal()
    try:
        store = SqlAlchemyCrawlStore(db)
        crawl = store.get_crawl(crawl_id)
        if crawl is None:
            return {"ok": False, "error": "crawl_not_found"}
        engine = PeacockCrawler(store=store)
        result = asyncio.run(
            engine.start(
                organisation_id=crawl.organisation_id,
                workspace_id=crawl.workspace_id,
                seed_url=crawl.seed_url,
                policy=crawl.policy,
                website_id=crawl.website_id,
                created_by=crawl.created_by,
                crawl_id=crawl.id,
            )
        )
        return {
            "ok": True,
            "crawl_id": result.id,
            "status": result.status,
            "progress": result.progress.to_dict(),
        }
    finally:
        db.close()
