"""Common publishing connector interface — extensible to any CMS."""

from __future__ import annotations

from typing import Protocol

from peacock_publishing.models import PublishRequest, PublishResult


class PublishingConnector(Protocol):
    name: str

    def is_configured(self) -> bool: ...

    async def publish(self, request: PublishRequest, *, confirm: bool) -> PublishResult: ...
