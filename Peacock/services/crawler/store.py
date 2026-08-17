"""In-memory and SQLAlchemy persistence for Peacock Crawler runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from crawler.extract import PageExtraction
from crawler.ports import CrawlProgress
from crawler.policy import CrawlPolicy


@dataclass
class StoredIssue:
    id: str
    code: str
    severity: str
    message: str
    page_url: str | None = None
    status: str = "open"


@dataclass
class StoredPage:
    id: str
    url: str
    canonical: str | None
    status_code: int | None
    title: str | None
    meta_description: str | None
    h1: list[str]
    h2: list[str]
    h3: list[str]
    body_text: str
    word_count: int
    internal_links: list[str]
    external_links: list[str]
    images: list[dict[str, str | None]]
    schema: list[dict[str, Any]]
    robots: str | None
    indexability: str
    crawl_depth: int
    content_hash: str | None
    content_type: str | None
    language: str | None
    is_js_heavy: bool
    redirect_chain: list[str]
    fetch_mode: str
    status: str
    is_near_duplicate: bool = False
    near_duplicate_of: str | None = None
    is_orphan_candidate: bool = False


@dataclass
class StoredCrawl:
    id: str
    organisation_id: str
    workspace_id: str
    website_id: str | None
    seed_url: str
    status: str
    policy: CrawlPolicy
    progress: CrawlProgress
    pages: dict[str, StoredPage] = field(default_factory=dict)
    issues: list[StoredIssue] = field(default_factory=list)
    control_command: str = "none"  # none|pause|resume|cancel
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_summary: str | None = None
    robots_raw: str | None = None
    sitemap_urls: list[str] = field(default_factory=list)
    created_by: str | None = None


class CrawlStore(Protocol):
    def create_crawl(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        seed_url: str,
        policy: CrawlPolicy,
        website_id: str | None = None,
        created_by: str | None = None,
    ) -> StoredCrawl: ...

    def get_crawl(self, crawl_id: str) -> StoredCrawl | None: ...

    def save_crawl(self, crawl: StoredCrawl) -> None: ...

    def upsert_page(self, crawl_id: str, page: StoredPage) -> None: ...

    def add_issue(self, crawl_id: str, issue: StoredIssue) -> None: ...

    def set_control_command(self, crawl_id: str, command: str) -> StoredCrawl | None: ...

    def list_failed_urls(self, crawl_id: str) -> list[str]: ...


class InMemoryCrawlStore:
    """Deterministic store for unit tests and local dry-runs."""

    def __init__(self) -> None:
        self._crawls: dict[str, StoredCrawl] = {}

    def create_crawl(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        seed_url: str,
        policy: CrawlPolicy,
        website_id: str | None = None,
        created_by: str | None = None,
    ) -> StoredCrawl:
        crawl = StoredCrawl(
            id=str(uuid4()),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            website_id=website_id,
            seed_url=seed_url,
            status="pending",
            policy=policy,
            progress=CrawlProgress(max_pages=policy.max_pages, status="pending"),
            created_by=created_by,
        )
        self._crawls[crawl.id] = crawl
        return crawl

    def get_crawl(self, crawl_id: str) -> StoredCrawl | None:
        return self._crawls.get(crawl_id)

    def save_crawl(self, crawl: StoredCrawl) -> None:
        self._crawls[crawl.id] = crawl

    def upsert_page(self, crawl_id: str, page: StoredPage) -> None:
        crawl = self._crawls[crawl_id]
        crawl.pages[page.url] = page

    def add_issue(self, crawl_id: str, issue: StoredIssue) -> None:
        crawl = self._crawls[crawl_id]
        crawl.issues.append(issue)
        crawl.progress.issues_found = len(crawl.issues)

    def set_control_command(self, crawl_id: str, command: str) -> StoredCrawl | None:
        crawl = self._crawls.get(crawl_id)
        if not crawl:
            return None
        crawl.control_command = command
        return crawl

    def list_failed_urls(self, crawl_id: str) -> list[str]:
        crawl = self._crawls[crawl_id]
        return [p.url for p in crawl.pages.values() if p.status == "failed"]


def page_from_extraction(
    extraction: PageExtraction,
    *,
    fetch_mode: str,
    status: str = "fetched",
) -> StoredPage:
    return StoredPage(
        id=str(uuid4()),
        url=extraction.final_url or extraction.url,
        canonical=extraction.canonical,
        status_code=extraction.status_code,
        title=extraction.title,
        meta_description=extraction.meta_description,
        h1=list(extraction.h1),
        h2=list(extraction.h2),
        h3=list(extraction.h3),
        body_text=extraction.body_text,
        word_count=extraction.word_count,
        internal_links=list(extraction.internal_links),
        external_links=list(extraction.external_links),
        images=[{"src": img.src, "alt": img.alt} for img in extraction.images],
        schema=list(extraction.schema_blocks),
        robots=extraction.robots,
        indexability=extraction.indexability,
        crawl_depth=extraction.crawl_depth,
        content_hash=extraction.content_hash,
        content_type=extraction.content_type,
        language=extraction.language,
        is_js_heavy=extraction.is_js_heavy,
        redirect_chain=list(extraction.redirect_chain),
        fetch_mode=fetch_mode,
        status=status,
    )
