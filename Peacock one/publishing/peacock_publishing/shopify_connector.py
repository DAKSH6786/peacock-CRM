"""Shopify connector — stub implementing the shared interface.

Configure via ``SHOPIFY_STORE_DOMAIN`` and ``SHOPIFY_ADMIN_API_TOKEN``
environment variables. Real blog-article creation is not implemented yet in
this deployment; the connector honestly reports ``not_configured`` /
``not_implemented`` rather than fabricating a publish result.
"""

from __future__ import annotations

import os

from peacock_publishing.models import PublishRequest, PublishResult


class ShopifyConnector:
    name = "shopify"

    def is_configured(self) -> bool:
        return bool(os.getenv("SHOPIFY_STORE_DOMAIN") and os.getenv("SHOPIFY_ADMIN_API_TOKEN"))

    async def publish(self, request: PublishRequest, *, confirm: bool) -> PublishResult:
        if not self.is_configured():
            return PublishResult(
                connector=self.name,
                published=False,
                status="not_configured",
                detail="Shopify connector requires SHOPIFY_STORE_DOMAIN and SHOPIFY_ADMIN_API_TOKEN environment variables.",
            )
        return PublishResult(
            connector=self.name,
            published=False,
            status="not_implemented",
            detail="Shopify blog-article creation is not implemented yet in this deployment — extend ShopifyConnector.publish().",
        )
