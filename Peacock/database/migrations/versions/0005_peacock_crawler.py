"""peacock crawler page fields and progress

Revision ID: 0005_peacock_crawler
Revises: 9b7d51fd6b52
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_peacock_crawler"
down_revision: Union[str, None] = "9b7d51fd6b52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("crawls", sa.Column("seed_url", sa.String(length=2048), nullable=True))
    op.add_column("crawls", sa.Column("job_id", sa.String(length=36), nullable=True))
    op.add_column("crawls", sa.Column("pages_discovered", sa.Integer(), server_default="0", nullable=False))
    op.add_column("crawls", sa.Column("pages_crawled", sa.Integer(), server_default="0", nullable=False))
    op.add_column("crawls", sa.Column("pages_failed", sa.Integer(), server_default="0", nullable=False))
    op.add_column("crawls", sa.Column("issues_found", sa.Integer(), server_default="0", nullable=False))
    op.add_column("crawls", sa.Column("control_command", sa.String(length=32), server_default="none", nullable=False))
    op.create_index("ix_crawls_job_id", "crawls", ["job_id"])

    op.add_column("crawl_pages", sa.Column("h1", sa.Text(), nullable=True))
    op.add_column("crawl_pages", sa.Column("h2", sa.Text(), nullable=True))
    op.add_column("crawl_pages", sa.Column("h3", sa.Text(), nullable=True))
    op.add_column("crawl_pages", sa.Column("body_text", sa.Text(), nullable=True))
    op.add_column("crawl_pages", sa.Column("internal_link_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("crawl_pages", sa.Column("external_link_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("crawl_pages", sa.Column("internal_links", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("crawl_pages", sa.Column("external_links", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("crawl_pages", sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("crawl_pages", sa.Column("schema_blocks", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("crawl_pages", sa.Column("robots", sa.String(length=255), nullable=True))
    op.add_column("crawl_pages", sa.Column("indexability", sa.String(length=64), nullable=True))
    op.add_column("crawl_pages", sa.Column("crawl_depth", sa.Integer(), server_default="0", nullable=False))
    op.add_column("crawl_pages", sa.Column("content_type", sa.String(length=128), nullable=True))
    op.add_column("crawl_pages", sa.Column("language", sa.String(length=32), nullable=True))
    op.add_column("crawl_pages", sa.Column("is_js_heavy", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("crawl_pages", sa.Column("redirect_chain", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("crawl_pages", sa.Column("fetch_mode", sa.String(length=32), server_default="httpx", nullable=False))
    op.add_column("crawl_pages", sa.Column("is_near_duplicate", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("crawl_pages", sa.Column("near_duplicate_of", sa.String(length=2048), nullable=True))
    op.add_column("crawl_pages", sa.Column("is_orphan_candidate", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.create_index("ix_crawl_pages_indexability", "crawl_pages", ["indexability"])
    op.create_index("ix_crawl_pages_crawl_depth", "crawl_pages", ["crawl_depth"])


def downgrade() -> None:
    op.drop_index("ix_crawl_pages_crawl_depth", table_name="crawl_pages")
    op.drop_index("ix_crawl_pages_indexability", table_name="crawl_pages")
    for col in [
        "is_orphan_candidate",
        "near_duplicate_of",
        "is_near_duplicate",
        "fetch_mode",
        "redirect_chain",
        "is_js_heavy",
        "language",
        "content_type",
        "crawl_depth",
        "indexability",
        "robots",
        "schema_blocks",
        "images",
        "external_links",
        "internal_links",
        "external_link_count",
        "internal_link_count",
        "body_text",
        "h3",
        "h2",
        "h1",
    ]:
        op.drop_column("crawl_pages", col)

    op.drop_index("ix_crawls_job_id", table_name="crawls")
    for col in [
        "control_command",
        "issues_found",
        "pages_failed",
        "pages_crawled",
        "pages_discovered",
        "job_id",
        "seed_url",
    ]:
        op.drop_column("crawls", col)
