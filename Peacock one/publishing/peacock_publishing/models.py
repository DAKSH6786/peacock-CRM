"""Publishing Connectors — architecture:

    Peacock One -> Publishing Connector -> CMS

Publishing always requires explicit approval (``confirm=True``) on a task
that has already reached "ready_to_publish" in the Peacock Experts workflow.
No connector here ever deletes content, modifies existing production pages,
purchases backlinks, or performs outreach.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PublishRequest:
    title: str
    body: str
    meta_description: str | None = None
    slug: str | None = None
    schema_json: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PublishResult:
    connector: str
    published: bool
    status: str  # draft_created | not_configured | requires_confirmation | error
    detail: str
    external_url: str | None = None
    external_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
