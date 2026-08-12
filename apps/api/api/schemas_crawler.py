from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WebsiteIngestRequest(BaseModel):
    url: str = Field(min_length=3, max_length=2048)
    name: str | None = Field(default=None, max_length=255)
    workspace_id: str | None = None


class WebsiteResponse(BaseModel):
    id: str
    name: str
    primary_domain: str
    root_url: str
    workspace_id: str
    organisation_id: str
    status: str


class CrawlStartRequest(BaseModel):
    url: str | None = Field(default=None, max_length=2048)
    website_id: str | None = None
    workspace_id: str | None = None
    # Policy is configurable — do not hardcode commercial plans in the engine.
    policy_preset: str | None = Field(
        default=None,
        description="Optional named preset (free_trial/starter/pro/enterprise) resolved at API boundary",
    )
    max_pages: int | None = Field(default=None, ge=1, le=1_000_000)
    policy: dict[str, Any] = Field(default_factory=dict)
    run_inline: bool = Field(
        default=True,
        description="When true (default for local/dev), run crawl inline; otherwise enqueue background job",
    )


class CrawlProgressResponse(BaseModel):
    pages_discovered: int
    pages_crawled: int
    pages_failed: int
    issues_found: int
    progress_percent: float
    max_pages: int
    status: str


class CrawlPageResponse(BaseModel):
    id: str
    url: str
    canonical: str | None = None
    status_code: int | None = None
    title: str | None = None
    meta_description: str | None = None
    h1: list[str] = Field(default_factory=list)
    h2: list[str] = Field(default_factory=list)
    h3: list[str] = Field(default_factory=list)
    body_text: str | None = None
    word_count: int = 0
    internal_links: list[str] = Field(default_factory=list)
    external_links: list[str] = Field(default_factory=list)
    images: list[dict[str, Any]] = Field(default_factory=list)
    schema_blocks: list[dict[str, Any]] = Field(default_factory=list)
    robots: str | None = None
    indexability: str | None = None
    crawl_depth: int = 0
    content_hash: str | None = None
    content_type: str | None = None
    language: str | None = None
    status: str
    is_js_heavy: bool = False
    is_near_duplicate: bool = False
    is_orphan_candidate: bool = False


class CrawlIssueResponse(BaseModel):
    id: str
    code: str
    severity: str
    message: str
    page_url: str | None = None
    status: str


class CrawlResponse(BaseModel):
    id: str
    website_id: str | None
    seed_url: str
    status: str
    organisation_id: str
    workspace_id: str
    progress: CrawlProgressResponse
    policy: dict[str, Any]
    error_summary: str | None = None
    pages: list[CrawlPageResponse] = Field(default_factory=list)
    issues: list[CrawlIssueResponse] = Field(default_factory=list)
