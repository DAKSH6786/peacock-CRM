"""Peacock Publishing Connectors.

    Peacock One -> Publishing Connector -> CMS

Extensible to WordPress, Webflow, Shopify, or a custom CMS. Publishing
always requires explicit approval (``confirm=True``); the WordPress
connector only ever creates drafts, and the default ``manual`` connector
never calls an external system at all.
"""

from peacock_publishing.models import PublishRequest, PublishResult
from peacock_publishing.registry import get_connector, list_connectors

__all__ = ["PublishRequest", "PublishResult", "get_connector", "list_connectors"]
