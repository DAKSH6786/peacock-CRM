"""Peacock Experts — human review/approval workflow for AI-generated work.

    AI Generated -> Human Assigned -> Review -> Changes Requested -> Revised
    -> Approved -> Ready to Publish

In-memory (process-local) task/review ledger — no destructive action is ever
taken automatically; publishing always requires an explicit approval on a
task in the "approved" or "ready_to_publish" state (see ``publishing``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

EXPERT_ROLES = (
    "seo_expert",
    "geo_expert",
    "writer",
    "editor",
    "researcher",
    "subject_matter_expert",
    "technical_seo_expert",
)

TASK_STATUSES = (
    "ai_generated",
    "human_assigned",
    "in_review",
    "changes_requested",
    "revised",
    "approved",
    "ready_to_publish",
)

_TRANSITIONS: dict[str, tuple[str, ...]] = {
    "ai_generated": ("human_assigned",),
    "human_assigned": ("in_review",),
    "in_review": ("changes_requested", "approved"),
    "changes_requested": ("revised",),
    "revised": ("in_review",),
    "approved": ("ready_to_publish",),
    "ready_to_publish": (),
}


def allowed_next_statuses(current: str) -> tuple[str, ...]:
    return _TRANSITIONS.get(current, ())


@dataclass(slots=True)
class Comment:
    author: str
    body: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VersionEntry:
    version: int
    content: str
    changed_by: str
    changed_at: str
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExpertTask:
    task_id: str
    title: str
    task_type: str  # content_brief | draft | fix | schema | internal_link | citation | technical
    content: str
    status: str = "ai_generated"
    assignee: str | None = None
    assignee_role: str | None = None
    comments: list[Comment] = field(default_factory=list)
    versions: list[VersionEntry] = field(default_factory=list)
    review_notes: list[str] = field(default_factory=list)
    approved_by: str | None = None
    approved_at: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "task_type": self.task_type,
            "content": self.content,
            "status": self.status,
            "assignee": self.assignee,
            "assignee_role": self.assignee_role,
            "comments": [c.to_dict() for c in self.comments],
            "versions": [v.to_dict() for v in self.versions],
            "review_notes": list(self.review_notes),
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
