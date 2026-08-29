"""Publishing connector registry — extensible without changing core code."""

from __future__ import annotations

from peacock_publishing.manual_connector import ManualApprovalConnector
from peacock_publishing.ports import PublishingConnector
from peacock_publishing.shopify_connector import ShopifyConnector
from peacock_publishing.webflow_connector import WebflowConnector
from peacock_publishing.wordpress_connector import WordPressConnector

_CONNECTORS: dict[str, PublishingConnector] = {
    "manual": ManualApprovalConnector(),
    "wordpress": WordPressConnector(),
    "webflow": WebflowConnector(),
    "shopify": ShopifyConnector(),
}


def get_connector(name: str) -> PublishingConnector:
    connector = _CONNECTORS.get(name)
    if connector is None:
        raise KeyError(f"Unknown publishing connector: {name}")
    return connector


def list_connectors() -> list[dict[str, object]]:
    return [{"name": name, "configured": c.is_configured()} for name, c in _CONNECTORS.items()]
