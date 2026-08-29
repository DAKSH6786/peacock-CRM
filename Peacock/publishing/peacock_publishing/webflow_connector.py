"""Webflow connector — stub implementing the shared interface.

Configure via ``WEBFLOW_API_TOKEN`` and ``WEBFLOW_COLLECTION_ID`` environment
variables. Real CMS-item creation is not implemented yet in this deployment;
the connector honestly reports ``not_configured`` / ``not_implemented``
rather than fabricating a publish result.
"""

from __future__ import annotations

import os

from peacock_publishing.models import PublishRequest, PublishResult


class WebflowConnector:
    name = "webflow"

    def is_configured(self) -> bool:
        return bool(os.getenv("WEBFLOW_API_TOKEN") and os.getenv("WEBFLOW_COLLECTION_ID"))

    async def publish(self, request: PublishRequest, *, confirm: bool) -> PublishResult:
        if not self.is_configured():
            return PublishResult(
                connector=self.name,
                published=False,
                status="not_configured",
                detail="Webflow connector requires WEBFLOW_API_TOKEN and WEBFLOW_COLLECTION_ID environment variables.",
            )
        return PublishResult(
            connector=self.name,
            published=False,
            status="not_implemented",
            detail="Webflow CMS-item creation is not implemented yet in this deployment — extend WebflowConnector.publish().",
        )
