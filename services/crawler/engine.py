"""Peacock Crawler — website ingestion and crawl orchestration."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from crawler.adapters.httpx_fetcher import HttpxFetcher
from crawler.adapters.playwright_fetcher import PlaywrightFetcher
from crawler.control import CONTROL_REGISTRY, CrawlControl
from crawler.extract import extract_page, near_duplicate
from crawler.policy import CrawlPolicy
from crawler.ports import BrowserFetcher, CrawlProgress, HttpFetcher
from crawler.robots import inspect_robots, is_allowed
from crawler.sitemap import discover_and_parse_sitemaps
from crawler.store import (
    CrawlStore,
    InMemoryCrawlStore,
    StoredCrawl,
    StoredIssue,
    StoredPage,
    page_from_extraction,
)
from crawler.url_utils import (
    UrlValidationError,
    assert_public_crawl_target,
    normalise_url,
    resolve_dns,
    validate_domain,
)


@dataclass(slots=True)
class QueueItem:
    url: str
    depth: int
    retries: int = 0


class PeacockCrawler:
    """Core crawl engine. Commercial plans are expressed only via ``CrawlPolicy``."""

    name = "Peacock Crawler"

    def __init__(
        self,
        store: CrawlStore | None = None,
        *,
        http_fetcher: HttpFetcher | None = None,
        browser_fetcher: BrowserFetcher | None = None,
    ) -> None:
        self.store = store or InMemoryCrawlStore()
        self.http_fetcher = http_fetcher or HttpxFetcher()
        self.browser_fetcher = browser_fetcher or PlaywrightFetcher()

    async def start(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        seed_url: str,
        policy: CrawlPolicy | None = None,
        website_id: str | None = None,
        created_by: str | None = None,
        crawl_id: str | None = None,
    ) -> StoredCrawl:
        policy = policy or CrawlPolicy()
        try:
            normalised = normalise_url(seed_url)
            validate_domain(normalised.hostname)
            resolved: list[str] = []
            if not normalised.is_ip_host and (policy.require_dns or not policy.allow_private_hosts):
                try:
                    resolved = resolve_dns(normalised.hostname)
                except OSError:
                    if policy.require_dns:
                        raise
                    resolved = []
            if not policy.allow_private_hosts:
                assert_public_crawl_target(normalised.hostname, resolved_ips=resolved)
            elif policy.require_dns and not normalised.is_ip_host and not resolved:
                resolve_dns(normalised.hostname)
        except (UrlValidationError, OSError) as exc:
            raise UrlValidationError(str(exc)) from exc

        if crawl_id:
            crawl = self.store.get_crawl(crawl_id)
            if crawl is None:
                raise KeyError(f"Unknown crawl: {crawl_id}")
        else:
            crawl = self.store.create_crawl(
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                seed_url=normalised.normalised,
                policy=policy,
                website_id=website_id,
                created_by=created_by,
            )

        control = CONTROL_REGISTRY.get_or_create(crawl.id)
        crawl.status = "running"
        crawl.started_at = crawl.started_at or datetime.now(UTC)
        crawl.progress.status = "running"
        crawl.progress.max_pages = policy.max_pages
        crawl.control_command = "none"
        self.store.save_crawl(crawl)

        try:
            await self._run(crawl, control)
        except Exception as exc:  # noqa: BLE001 — surface as crawl failure, never crash worker process
            crawl = self.store.get_crawl(crawl.id) or crawl
            crawl.status = "failed"
            crawl.error_summary = str(exc)
            crawl.completed_at = datetime.now(UTC)
            crawl.progress.status = "failed"
            self.store.add_issue(
                crawl.id,
                StoredIssue(
                    id=str(uuid4()),
                    code="crawl_crashed",
                    severity="critical",
                    message=f"Crawl aborted safely: {exc}",
                ),
            )
            self.store.save_crawl(crawl)
        finally:
            CONTROL_REGISTRY.drop(crawl.id)

        return self.store.get_crawl(crawl.id) or crawl

    async def _run(self, crawl: StoredCrawl, control: CrawlControl) -> None:
        policy = crawl.policy
        seed = crawl.seed_url
        http = (
            self.http_fetcher
            if not isinstance(self.http_fetcher, HttpxFetcher)
            else HttpxFetcher(
                user_agent=policy.user_agent,
                follow_redirects=policy.follow_redirects,
                max_redirects=policy.max_redirects,
            )
        )

        robots = await inspect_robots(
            seed,
            http,
            user_agent=policy.user_agent,
            timeout_seconds=min(15.0, policy.fetch_timeout_seconds),
        )
        crawl.robots_raw = robots.raw_text
        if robots.fetched and not robots.can_fetch_seed and policy.respect_robots:
            self.store.add_issue(
                crawl.id,
                StoredIssue(
                    id=str(uuid4()),
                    code="robots_disallow_seed",
                    severity="high",
                    message=f"robots.txt disallows crawling seed URL for {policy.user_agent}",
                    page_url=seed,
                ),
            )
            crawl.status = "completed"
            crawl.progress.status = "completed"
            crawl.completed_at = datetime.now(UTC)
            self.store.save_crawl(crawl)
            return

        discovered: list[str] = [seed]
        if policy.discover_sitemaps and policy.parse_sitemaps:
            sitemap = await discover_and_parse_sitemaps(
                seed,
                http,
                robots_sitemaps=robots.sitemap_urls,
                timeout_seconds=policy.fetch_timeout_seconds,
                max_urls=policy.max_pages * 5,
            )
            crawl.sitemap_urls = sitemap.sitemap_urls
            for err in sitemap.errors[:20]:
                self.store.add_issue(
                    crawl.id,
                    StoredIssue(
                        id=str(uuid4()),
                        code="sitemap_error",
                        severity="low",
                        message=err,
                    ),
                )
            for url in sitemap.page_urls:
                if policy.same_host_only and normalise_url(url).hostname != normalise_url(seed).hostname:
                    continue
                discovered.append(url)

        # Deduplicate while preserving order
        discovered = list(dict.fromkeys(discovered))
        crawl.progress.pages_discovered = len(discovered)
        self.store.save_crawl(crawl)

        queue: deque[QueueItem] = deque(QueueItem(url=u, depth=0 if u == seed else 1) for u in discovered)
        seen: set[str] = set()
        inbound_counts: dict[str, int] = {seed: 1}

        while queue:
            self._apply_db_control(crawl, control)
            if control.is_cancelled:
                crawl.status = "cancelled"
                crawl.progress.status = "cancelled"
                crawl.completed_at = datetime.now(UTC)
                self.store.save_crawl(crawl)
                return
            while control.is_paused:
                crawl.status = "paused"
                crawl.progress.status = "paused"
                self.store.save_crawl(crawl)
                await asyncio.sleep(0.15)
                self._apply_db_control(crawl, control)
                if control.is_cancelled:
                    break
            if control.is_cancelled:
                continue
            if crawl.status == "paused":
                crawl.status = "running"
                crawl.progress.status = "running"

            if crawl.progress.pages_crawled >= policy.max_pages:
                break

            item = queue.popleft()
            if item.url in seen:
                continue
            if item.depth > policy.max_depth:
                continue
            if not is_allowed(robots, item.url, user_agent=policy.user_agent, respect=policy.respect_robots):
                self.store.add_issue(
                    crawl.id,
                    StoredIssue(
                        id=str(uuid4()),
                        code="robots_disallow",
                        severity="medium",
                        message=f"Skipped by robots.txt: {item.url}",
                        page_url=item.url,
                    ),
                )
                continue

            seen.add(item.url)
            try:
                page, extraction = await self._fetch_and_extract(item, policy, http, seed)
            except Exception as exc:  # noqa: BLE001
                await self._record_failure(crawl, item, str(exc), queue, policy)
                continue

            if page.status == "failed" and (page.status_code in {0, None} or not page.title):
                # Transport failures — retry then count as failed. HTTP 4xx/5xx still persist below.
                if page.status_code in {0, None}:
                    await self._record_failure(
                        crawl,
                        item,
                        page.body_text or f"HTTP {page.status_code}",
                        queue,
                        policy,
                        page=page,
                    )
                    continue

            # Duplicate / near-duplicate detection
            for existing in crawl.pages.values():
                if existing.content_hash and existing.content_hash == page.content_hash and existing.url != page.url:
                    page.is_near_duplicate = True
                    page.near_duplicate_of = existing.url
                    self.store.add_issue(
                        crawl.id,
                        StoredIssue(
                            id=str(uuid4()),
                            code="duplicate_content",
                            severity="medium",
                            message=f"Duplicate content hash of {existing.url}",
                            page_url=page.url,
                        ),
                    )
                    break
                if (
                    not page.is_near_duplicate
                    and existing.body_text
                    and near_duplicate(
                        existing.body_text,
                        page.body_text,
                        threshold=policy.near_duplicate_threshold,
                    )
                    and existing.url != page.url
                ):
                    page.is_near_duplicate = True
                    page.near_duplicate_of = existing.url
                    self.store.add_issue(
                        crawl.id,
                        StoredIssue(
                            id=str(uuid4()),
                            code="near_duplicate_content",
                            severity="low",
                            message=f"Near-duplicate of {existing.url}",
                            page_url=page.url,
                        ),
                    )
                    break

            if page.status_code and page.status_code >= 400:
                page.status = "failed"
                self.store.add_issue(
                    crawl.id,
                    StoredIssue(
                        id=str(uuid4()),
                        code="broken_page",
                        severity="high" if page.status_code >= 500 else "medium",
                        message=f"Broken page HTTP {page.status_code}",
                        page_url=page.url,
                    ),
                )
                self.store.upsert_page(crawl.id, page)
                crawl.progress.pages_failed += 1
                crawl.progress.pages_discovered = max(
                    crawl.progress.pages_discovered,
                    len(seen) + len(queue),
                )
                crawl.progress.issues_found = len(crawl.issues)
                self.store.save_crawl(crawl)
                continue

            if len(page.redirect_chain) > 2:
                self.store.add_issue(
                    crawl.id,
                    StoredIssue(
                        id=str(uuid4()),
                        code="redirect_chain",
                        severity="low",
                        message=" → ".join(page.redirect_chain),
                        page_url=page.url,
                    ),
                )

            if page.is_js_heavy:
                self.store.add_issue(
                    crawl.id,
                    StoredIssue(
                        id=str(uuid4()),
                        code="js_heavy_page",
                        severity="info",
                        message="Page looks JavaScript-heavy",
                        page_url=page.url,
                    ),
                )

            self.store.upsert_page(crawl.id, page)
            crawl.progress.pages_crawled += 1
            crawl.progress.pages_discovered = max(
                crawl.progress.pages_discovered,
                len(seen) + len(queue),
            )
            crawl.progress.issues_found = len(crawl.issues)
            self.store.save_crawl(crawl)

            # Enqueue internal links
            for link in extraction.internal_links:
                inbound_counts[link] = inbound_counts.get(link, 0) + 1
                if link in seen:
                    continue
                if policy.same_host_only:
                    try:
                        if normalise_url(link).hostname != normalise_url(seed).hostname:
                            continue
                    except UrlValidationError:
                        continue
                if item.depth + 1 > policy.max_depth:
                    continue
                if crawl.progress.pages_crawled + len(queue) >= policy.max_pages * 3:
                    break
                queue.append(QueueItem(url=link, depth=item.depth + 1))
                crawl.progress.pages_discovered = max(
                    crawl.progress.pages_discovered,
                    len(seen) + len(queue),
                )

            self.store.save_crawl(crawl)

        # Orphan candidates: discovered via sitemap / links but never linked from crawled pages
        crawled_urls = set(crawl.pages.keys())
        for url, count in inbound_counts.items():
            if count <= 0 and url in crawled_urls:
                page = crawl.pages[url]
                page.is_orphan_candidate = True
                self.store.upsert_page(crawl.id, page)
        for url, page in crawl.pages.items():
            if url != seed and inbound_counts.get(url, 0) <= 1 and page.crawl_depth > 0:
                # pages only referenced once from sitemap seed path are soft orphan candidates
                if inbound_counts.get(url, 0) == 0:
                    page.is_orphan_candidate = True
                    self.store.upsert_page(crawl.id, page)
                    self.store.add_issue(
                        crawl.id,
                        StoredIssue(
                            id=str(uuid4()),
                            code="orphan_candidate",
                            severity="low",
                            message="Page has no inbound internal links from crawled set",
                            page_url=url,
                        ),
                    )

        crawl = self.store.get_crawl(crawl.id) or crawl
        if crawl.status not in {"cancelled", "failed"}:
            crawl.status = "completed"
            crawl.progress.status = "completed"
            crawl.completed_at = datetime.now(UTC)
            crawl.progress.issues_found = len(crawl.issues)
            self.store.save_crawl(crawl)

    async def _fetch_and_extract(
        self,
        item: QueueItem,
        policy: CrawlPolicy,
        http: HttpFetcher,
        seed: str,
    ) -> tuple[StoredPage, Any]:
        result = await http.fetch(item.url, timeout_seconds=policy.fetch_timeout_seconds)
        fetch_mode = "httpx"
        if result.error and result.status_code == 0:
            page = StoredPage(
                id=str(uuid4()),
                url=item.url,
                canonical=None,
                status_code=0,
                title=None,
                meta_description=None,
                h1=[],
                h2=[],
                h3=[],
                body_text=result.error or "",
                word_count=0,
                internal_links=[],
                external_links=[],
                images=[],
                schema=[],
                robots=None,
                indexability="non_indexable_status",
                crawl_depth=item.depth,
                content_hash=None,
                content_type=None,
                language=None,
                is_js_heavy=False,
                redirect_chain=result.redirect_chain or [item.url],
                fetch_mode=fetch_mode,
                status="failed",
            )
            return page, None

        extraction = extract_page(
            request_url=item.url,
            final_url=result.url or item.url,
            status_code=result.status_code,
            html=result.html,
            headers=result.headers,
            seed_host_url=seed,
            crawl_depth=item.depth,
            redirect_chain=result.redirect_chain,
            js_heavy_script_threshold=policy.js_heavy_script_threshold,
            js_heavy_body_char_threshold=policy.js_heavy_body_char_threshold,
            max_body_chars=policy.max_body_chars if policy.store_body_text else 0,
        )

        should_render = policy.force_js_render or (
            policy.allow_js_render and extraction.is_js_heavy and self.browser_fetcher.available
        )
        if should_render:
            rendered = await self.browser_fetcher.fetch(
                item.url, timeout_seconds=policy.render_timeout_seconds
            )
            if not rendered.error and rendered.html:
                fetch_mode = "playwright"
                extraction = extract_page(
                    request_url=item.url,
                    final_url=rendered.url or item.url,
                    status_code=rendered.status_code,
                    html=rendered.html,
                    headers=rendered.headers,
                    seed_host_url=seed,
                    crawl_depth=item.depth,
                    redirect_chain=rendered.redirect_chain or result.redirect_chain,
                    js_heavy_script_threshold=policy.js_heavy_script_threshold,
                    js_heavy_body_char_threshold=policy.js_heavy_body_char_threshold,
                    max_body_chars=policy.max_body_chars if policy.store_body_text else 0,
                )

        page_status = "failed" if extraction.status_code >= 400 else "fetched"
        page = page_from_extraction(extraction, fetch_mode=fetch_mode, status=page_status)
        return page, extraction

    async def _record_failure(
        self,
        crawl: StoredCrawl,
        item: QueueItem,
        message: str,
        queue: deque[QueueItem],
        policy: CrawlPolicy,
        page: StoredPage | None = None,
    ) -> None:
        if item.retries < policy.max_retries_per_url:
            queue.append(QueueItem(url=item.url, depth=item.depth, retries=item.retries + 1))
            await asyncio.sleep(policy.retry_backoff_seconds)
            return
        if page is None:
            page = StoredPage(
                id=str(uuid4()),
                url=item.url,
                canonical=None,
                status_code=0,
                title=None,
                meta_description=None,
                h1=[],
                h2=[],
                h3=[],
                body_text=message,
                word_count=0,
                internal_links=[],
                external_links=[],
                images=[],
                schema=[],
                robots=None,
                indexability="non_indexable_status",
                crawl_depth=item.depth,
                content_hash=None,
                content_type=None,
                language=None,
                is_js_heavy=False,
                redirect_chain=[item.url],
                fetch_mode="httpx",
                status="failed",
            )
        else:
            page.status = "failed"
        self.store.upsert_page(crawl.id, page)
        self.store.add_issue(
            crawl.id,
            StoredIssue(
                id=str(uuid4()),
                code="fetch_failed",
                severity="high",
                message=message,
                page_url=item.url,
            ),
        )
        crawl.progress.pages_failed += 1
        crawl.progress.issues_found = len(crawl.issues)
        self.store.save_crawl(crawl)

    def _apply_db_control(self, crawl: StoredCrawl, control: CrawlControl) -> None:
        fresh = self.store.get_crawl(crawl.id)
        if fresh is None:
            return
        command = fresh.control_command
        if command == "pause":
            control.pause()
        elif command == "resume":
            control.resume()
            fresh.control_command = "none"
            self.store.save_crawl(fresh)
        elif command == "cancel":
            control.cancel()

    def progress(self, crawl_id: str) -> CrawlProgress:
        crawl = self.store.get_crawl(crawl_id)
        if crawl is None:
            raise KeyError(crawl_id)
        return crawl.progress

    def pause(self, crawl_id: str) -> StoredCrawl:
        crawl = self.store.set_control_command(crawl_id, "pause")
        if crawl is None:
            raise KeyError(crawl_id)
        CONTROL_REGISTRY.get_or_create(crawl_id).pause()
        crawl.status = "paused"
        crawl.progress.status = "paused"
        self.store.save_crawl(crawl)
        return crawl

    def resume(self, crawl_id: str) -> StoredCrawl:
        crawl = self.store.set_control_command(crawl_id, "resume")
        if crawl is None:
            raise KeyError(crawl_id)
        CONTROL_REGISTRY.get_or_create(crawl_id).resume()
        crawl.status = "running"
        crawl.progress.status = "running"
        self.store.save_crawl(crawl)
        return crawl

    def cancel(self, crawl_id: str) -> StoredCrawl:
        crawl = self.store.set_control_command(crawl_id, "cancel")
        if crawl is None:
            raise KeyError(crawl_id)
        CONTROL_REGISTRY.get_or_create(crawl_id).cancel()
        crawl.status = "cancelled"
        crawl.progress.status = "cancelled"
        crawl.completed_at = datetime.now(UTC)
        self.store.save_crawl(crawl)
        return crawl

    async def restart(
        self,
        crawl_id: str,
        *,
        organisation_id: str,
        workspace_id: str,
    ) -> StoredCrawl:
        previous = self.store.get_crawl(crawl_id)
        if previous is None:
            raise KeyError(crawl_id)
        return await self.start(
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            seed_url=previous.seed_url,
            policy=previous.policy,
            website_id=previous.website_id,
            created_by=previous.created_by,
        )

    async def retry_failed(self, crawl_id: str) -> StoredCrawl:
        crawl = self.store.get_crawl(crawl_id)
        if crawl is None:
            raise KeyError(crawl_id)
        failed = self.store.list_failed_urls(crawl_id)
        if not failed:
            return crawl

        control = CONTROL_REGISTRY.get_or_create(crawl.id)
        crawl.status = "running"
        crawl.progress.status = "running"
        crawl.control_command = "none"
        self.store.save_crawl(crawl)

        http = HttpxFetcher(
            user_agent=crawl.policy.user_agent,
            follow_redirects=crawl.policy.follow_redirects,
            max_redirects=crawl.policy.max_redirects,
        )
        for url in failed:
            if control.is_cancelled:
                break
            page = crawl.pages.get(url)
            depth = page.crawl_depth if page else 0
            item = QueueItem(url=url, depth=depth, retries=0)
            try:
                new_page, _extraction = await self._fetch_and_extract(item, crawl.policy, http, crawl.seed_url)
            except Exception as exc:  # noqa: BLE001
                self.store.add_issue(
                    crawl.id,
                    StoredIssue(
                        id=str(uuid4()),
                        code="retry_failed",
                        severity="high",
                        message=str(exc),
                        page_url=url,
                    ),
                )
                continue
            if new_page.status != "failed":
                # replace failed page
                if crawl.progress.pages_failed > 0:
                    crawl.progress.pages_failed -= 1
                crawl.progress.pages_crawled += 1
            self.store.upsert_page(crawl.id, new_page)
            self.store.save_crawl(crawl)

        crawl = self.store.get_crawl(crawl.id) or crawl
        crawl.status = "completed"
        crawl.progress.status = "completed"
        crawl.completed_at = datetime.now(UTC)
        self.store.save_crawl(crawl)
        CONTROL_REGISTRY.drop(crawl.id)
        return crawl
