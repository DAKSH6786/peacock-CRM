"""SQLAlchemy-backed crawl store used by API workers."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from crawler.policy import CrawlPolicy
from crawler.ports import CrawlProgress
from crawler.store import StoredCrawl, StoredIssue, StoredPage
from db_models import Crawl, CrawlIssue, CrawlLink, CrawlPage, Website
from db_models.base import new_uuid


def _join_headings(values: list[str]) -> str | None:
    if not values:
        return None
    return "\n".join(values)


def _split_headings(value: str | None) -> list[str]:
    if not value:
        return []
    return [line for line in value.split("\n") if line]


class SqlAlchemyCrawlStore:
    def __init__(self, session: Session) -> None:
        self.session = session

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
        if website_id is None:
            raise ValueError("website_id is required for SQL crawl persistence")
        row = Crawl(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            website_id=website_id,
            created_by=created_by,
            seed_url=seed_url,
            status="pending",
            trigger="manual",
            control_command="none",
            config=policy.to_dict(),
            pages_discovered=0,
            pages_crawled=0,
            pages_failed=0,
            issues_found=0,
            page_count=0,
        )
        self.session.add(row)
        self.session.commit()
        return self._to_stored(row, policy=policy)

    def get_crawl(self, crawl_id: str) -> StoredCrawl | None:
        row = self.session.get(Crawl, crawl_id)
        if row is None:
            return None
        return self._hydrate(row)

    def save_crawl(self, crawl: StoredCrawl) -> None:
        row = self.session.get(Crawl, crawl.id)
        if row is None:
            return
        row.status = crawl.status
        row.seed_url = crawl.seed_url
        row.control_command = crawl.control_command
        row.started_at = crawl.started_at
        row.completed_at = crawl.completed_at
        row.error_summary = crawl.error_summary
        row.pages_discovered = crawl.progress.pages_discovered
        row.pages_crawled = crawl.progress.pages_crawled
        row.pages_failed = crawl.progress.pages_failed
        row.issues_found = crawl.progress.issues_found
        row.page_count = crawl.progress.pages_crawled
        row.config = {
            **(row.config or {}),
            **crawl.policy.to_dict(),
            "robots_raw": crawl.robots_raw,
            "sitemap_urls": crawl.sitemap_urls,
        }
        self.session.commit()

    def upsert_page(self, crawl_id: str, page: StoredPage) -> None:
        crawl = self.session.get(Crawl, crawl_id)
        if crawl is None:
            return
        existing = self.session.scalar(
            select(CrawlPage).where(CrawlPage.crawl_id == crawl_id, CrawlPage.url == page.url)
        )
        if existing is None:
            existing = CrawlPage(
                id=page.id or new_uuid(),
                organisation_id=crawl.organisation_id,
                workspace_id=crawl.workspace_id,
                crawl_id=crawl_id,
                url=page.url,
            )
            self.session.add(existing)

        existing.canonical_url = page.canonical
        existing.status_code = page.status_code
        existing.title = page.title
        existing.meta_description = page.meta_description
        existing.h1 = _join_headings(page.h1)
        existing.h2 = _join_headings(page.h2)
        existing.h3 = _join_headings(page.h3)
        existing.body_text = page.body_text
        existing.word_count = page.word_count
        existing.internal_link_count = len(page.internal_links)
        existing.external_link_count = len(page.external_links)
        existing.internal_links = page.internal_links
        existing.external_links = page.external_links
        existing.images = page.images
        existing.schema_blocks = page.schema
        existing.robots = page.robots
        existing.indexability = page.indexability
        existing.crawl_depth = page.crawl_depth
        existing.content_hash = page.content_hash
        existing.content_type = page.content_type
        existing.language = page.language
        existing.is_js_heavy = page.is_js_heavy
        existing.redirect_chain = page.redirect_chain
        existing.fetch_mode = page.fetch_mode
        existing.is_near_duplicate = page.is_near_duplicate
        existing.near_duplicate_of = page.near_duplicate_of
        existing.is_orphan_candidate = page.is_orphan_candidate
        existing.fetched_at = datetime.now(UTC)
        existing.status = page.status
        self.session.flush()

        # Replace outbound link rows for a clean snapshot
        for link in list(existing.outbound_links):
            self.session.delete(link)
        for href in page.internal_links:
            self.session.add(
                CrawlLink(
                    id=new_uuid(),
                    organisation_id=crawl.organisation_id,
                    workspace_id=crawl.workspace_id,
                    crawl_id=crawl_id,
                    from_page_id=existing.id,
                    to_url=href,
                    is_internal=True,
                )
            )
        for href in page.external_links:
            self.session.add(
                CrawlLink(
                    id=new_uuid(),
                    organisation_id=crawl.organisation_id,
                    workspace_id=crawl.workspace_id,
                    crawl_id=crawl_id,
                    from_page_id=existing.id,
                    to_url=href,
                    is_internal=False,
                )
            )
        self.session.commit()

    def add_issue(self, crawl_id: str, issue: StoredIssue) -> None:
        crawl = self.session.get(Crawl, crawl_id)
        if crawl is None:
            return
        page_id = None
        if issue.page_url:
            page = self.session.scalar(
                select(CrawlPage).where(CrawlPage.crawl_id == crawl_id, CrawlPage.url == issue.page_url)
            )
            page_id = page.id if page else None
        self.session.add(
            CrawlIssue(
                id=issue.id or new_uuid(),
                organisation_id=crawl.organisation_id,
                workspace_id=crawl.workspace_id,
                crawl_id=crawl_id,
                page_id=page_id,
                code=issue.code,
                severity=issue.severity,
                message=issue.message,
                status=issue.status,
            )
        )
        crawl.issues_found = (crawl.issues_found or 0) + 1
        self.session.commit()

    def set_control_command(self, crawl_id: str, command: str) -> StoredCrawl | None:
        row = self.session.get(Crawl, crawl_id)
        if row is None:
            return None
        row.control_command = command
        self.session.commit()
        return self._hydrate(row)

    def list_failed_urls(self, crawl_id: str) -> list[str]:
        rows = self.session.scalars(
            select(CrawlPage.url).where(CrawlPage.crawl_id == crawl_id, CrawlPage.status == "failed")
        ).all()
        return list(rows)

    def _hydrate(self, row: Crawl) -> StoredCrawl:
        policy = CrawlPolicy.from_mapping(row.config or {})
        stored = self._to_stored(row, policy=policy)
        pages = self.session.scalars(select(CrawlPage).where(CrawlPage.crawl_id == row.id)).all()
        for page in pages:
            stored.pages[page.url] = StoredPage(
                id=page.id,
                url=page.url,
                canonical=page.canonical_url,
                status_code=page.status_code,
                title=page.title,
                meta_description=page.meta_description,
                h1=_split_headings(page.h1),
                h2=_split_headings(page.h2),
                h3=_split_headings(page.h3),
                body_text=page.body_text or "",
                word_count=page.word_count,
                internal_links=list(page.internal_links or []),
                external_links=list(page.external_links or []),
                images=list(page.images or []),
                schema=list(page.schema_blocks or []),
                robots=page.robots,
                indexability=page.indexability or "unknown",
                crawl_depth=page.crawl_depth,
                content_hash=page.content_hash,
                content_type=page.content_type,
                language=page.language,
                is_js_heavy=page.is_js_heavy,
                redirect_chain=list(page.redirect_chain or []),
                fetch_mode=page.fetch_mode,
                status=page.status,
                is_near_duplicate=page.is_near_duplicate,
                near_duplicate_of=page.near_duplicate_of,
                is_orphan_candidate=page.is_orphan_candidate,
            )
        issues = self.session.scalars(select(CrawlIssue).where(CrawlIssue.crawl_id == row.id)).all()
        page_urls = {p.id: p.url for p in pages}
        stored.issues = [
            StoredIssue(
                id=issue.id,
                code=issue.code,
                severity=issue.severity,
                message=issue.message,
                page_url=page_urls.get(issue.page_id) if issue.page_id else None,
                status=issue.status,
            )
            for issue in issues
        ]
        cfg = row.config or {}
        stored.robots_raw = cfg.get("robots_raw")
        stored.sitemap_urls = list(cfg.get("sitemap_urls") or [])
        return stored

    def _to_stored(self, row: Crawl, *, policy: CrawlPolicy) -> StoredCrawl:
        return StoredCrawl(
            id=row.id,
            organisation_id=row.organisation_id,
            workspace_id=row.workspace_id,
            website_id=row.website_id,
            seed_url=row.seed_url or "",
            status=row.status,
            policy=policy,
            progress=CrawlProgress(
                pages_discovered=row.pages_discovered,
                pages_crawled=row.pages_crawled,
                pages_failed=row.pages_failed,
                issues_found=row.issues_found,
                max_pages=policy.max_pages,
                status=row.status,
            ),
            control_command=row.control_command,
            started_at=row.started_at,
            completed_at=row.completed_at,
            error_summary=row.error_summary,
            created_by=row.created_by,
        )


def ensure_website_for_url(
    session: Session,
    *,
    organisation_id: str,
    workspace_id: str,
    url: str,
    created_by: str | None = None,
) -> Website:
    from crawler.url_utils import normalise_url

    normalised = normalise_url(url)
    existing = session.scalar(
        select(Website).where(
            Website.workspace_id == workspace_id,
            Website.primary_domain == normalised.hostname,
        )
    )
    if existing:
        return existing
    website = Website(
        id=new_uuid(),
        organisation_id=organisation_id,
        workspace_id=workspace_id,
        created_by=created_by,
        name=normalised.hostname,
        primary_domain=normalised.hostname,
        root_url=f"{normalised.scheme}://{normalised.hostname}/",
        status="active",
    )
    session.add(website)
    session.commit()
    return website
