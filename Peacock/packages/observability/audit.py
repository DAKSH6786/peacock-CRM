from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from observability.logging import get_logger


@dataclass(slots=True)
class AuditEvent:
    organisation_id: str
    actor_user_id: str | None
    action: str
    resource_type: str
    resource_id: str | None = None
    workspace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AuditSink(Protocol):
    def write(self, event: AuditEvent) -> None: ...


class LoggingAuditSink:
    def write(self, event: AuditEvent) -> None:
        get_logger("audit").info(
            "audit_event",
            organisation_id=event.organisation_id,
            actor_user_id=event.actor_user_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            workspace_id=event.workspace_id,
            metadata=event.metadata,
        )


class AuditLogger:
    def __init__(self, sink: AuditSink | None = None) -> None:
        self._sink = sink or LoggingAuditSink()

    def log(self, event: AuditEvent) -> None:
        self._sink.write(event)
