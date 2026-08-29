"""Peacock Experts service — in-memory task/review workflow (process-local)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from peacock_experts.models import Comment, ExpertTask, VersionEntry, allowed_next_statuses

_TASKS: dict[str, ExpertTask] = {}


def create_task(*, title: str, task_type: str, content: str) -> ExpertTask:
    task = ExpertTask(task_id=str(uuid4()), title=title, task_type=task_type, content=content)
    task.versions.append(VersionEntry(version=1, content=content, changed_by="peacock_ai", changed_at=task.created_at, note="AI generated"))
    _TASKS[task.task_id] = task
    return task


def assign_task(task_id: str, *, assignee: str, assignee_role: str) -> ExpertTask:
    task = _get(task_id)
    task.assignee = assignee
    task.assignee_role = assignee_role
    _transition(task, "human_assigned")
    return task


def add_comment(task_id: str, *, author: str, body: str) -> ExpertTask:
    task = _get(task_id)
    task.comments.append(Comment(author=author, body=body, created_at=datetime.now(tz=UTC).isoformat()))
    task.updated_at = datetime.now(tz=UTC).isoformat()
    return task


def request_changes(task_id: str, *, reviewer: str, note: str) -> ExpertTask:
    task = _get(task_id)
    task.review_notes.append(f"{reviewer}: {note}")
    _transition(task, "changes_requested")
    return task


def submit_revision(task_id: str, *, author: str, content: str, note: str | None = None) -> ExpertTask:
    task = _get(task_id)
    task.content = content
    next_version = (task.versions[-1].version + 1) if task.versions else 1
    task.versions.append(
        VersionEntry(version=next_version, content=content, changed_by=author, changed_at=datetime.now(tz=UTC).isoformat(), note=note)
    )
    _transition(task, "revised")
    _transition(task, "in_review")
    return task


def start_review(task_id: str) -> ExpertTask:
    task = _get(task_id)
    _transition(task, "in_review")
    return task


def approve_task(task_id: str, *, approver: str) -> ExpertTask:
    task = _get(task_id)
    task.approved_by = approver
    task.approved_at = datetime.now(tz=UTC).isoformat()
    _transition(task, "approved")
    return task


def mark_ready_to_publish(task_id: str) -> ExpertTask:
    task = _get(task_id)
    if task.status != "approved":
        raise ValueError("Task must be approved before it can be marked ready to publish.")
    _transition(task, "ready_to_publish")
    return task


def get_task(task_id: str) -> ExpertTask | None:
    return _TASKS.get(task_id)


def list_tasks(status: str | None = None, assignee: str | None = None) -> list[ExpertTask]:
    values = list(_TASKS.values())
    if status:
        values = [t for t in values if t.status == status]
    if assignee:
        values = [t for t in values if t.assignee == assignee]
    return sorted(values, key=lambda t: t.updated_at, reverse=True)


def _get(task_id: str) -> ExpertTask:
    task = _TASKS.get(task_id)
    if task is None:
        raise KeyError(f"Unknown expert task: {task_id}")
    return task


def _transition(task: ExpertTask, next_status: str) -> None:
    allowed = allowed_next_statuses(task.status)
    if next_status not in allowed and next_status != task.status:
        raise ValueError(f"Cannot move task from '{task.status}' to '{next_status}' (allowed: {allowed}).")
    task.status = next_status
    task.updated_at = datetime.now(tz=UTC).isoformat()
