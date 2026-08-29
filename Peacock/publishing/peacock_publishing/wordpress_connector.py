"""WordPress connector — real WP REST API integration, drafts only.

Configured via environment variables (never hardcoded):

    WORDPRESS_URL             e.g. https://example.com
    WORDPRESS_USERNAME        WordPress username
    WORDPRESS_APP_PASSWORD    WordPress "Application Password"

Even with ``confirm=True``, this connector only ever creates a **draft**
post via the WP REST API (``status=draft``) — it never sets a post live,
deletes anything, or modifies existing content. A human still has to
publish the draft from inside WordPress.
"""

from __future__ import annotations

import os

import httpx

from peacock_publishing.models import PublishRequest, PublishResult


class WordPressConnector:
    name = "wordpress"

    def __init__(self) -> None:
        self._base_url = (os.getenv("WORDPRESS_URL") or "").rstrip("/")
        self._username = os.getenv("WORDPRESS_USERNAME") or ""
        self._app_password = os.getenv("WORDPRESS_APP_PASSWORD") or ""

    def is_configured(self) -> bool:
        return bool(self._base_url and self._username and self._app_password)

    async def publish(self, request: PublishRequest, *, confirm: bool) -> PublishResult:
        if not self.is_configured():
            return PublishResult(
                connector=self.name,
                published=False,
                status="not_configured",
                detail=(
                    "WordPress connector requires WORDPRESS_URL, WORDPRESS_USERNAME, and "
                    "WORDPRESS_APP_PASSWORD environment variables."
                ),
            )
        if not confirm:
            return PublishResult(
                connector=self.name,
                published=False,
                status="requires_confirmation",
                detail="Set confirm=true to create a draft post in WordPress.",
            )

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                auth=(self._username, self._app_password),
                timeout=15.0,
            ) as client:
                response = await client.post(
                    "/wp-json/wp/v2/posts",
                    json={
                        "title": request.title,
                        "content": request.body,
                        "excerpt": request.meta_description or "",
                        "slug": request.slug or "",
                        "status": "draft",  # never publish live automatically
                    },
                )
            if response.status_code >= 400:
                return PublishResult(
                    connector=self.name,
                    published=False,
                    status="error",
                    detail=f"WordPress REST API returned HTTP {response.status_code}: {response.text[:300]}",
                )
            payload = response.json()
            return PublishResult(
                connector=self.name,
                published=False,
                status="draft_created",
                detail="Draft post created in WordPress — review and publish it manually from the WordPress admin.",
                external_url=payload.get("link"),
                external_id=str(payload.get("id")) if payload.get("id") is not None else None,
            )
        except Exception as exc:  # noqa: BLE001 — never crash the growth loop on a connector error
            return PublishResult(
                connector=self.name,
                published=False,
                status="error",
                detail=f"WordPress connector error: {exc}",
            )
