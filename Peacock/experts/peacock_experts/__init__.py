"""Peacock Experts — human review/approval layer for AI-generated work.

    AI Generated -> Human Assigned -> Review -> Changes Requested -> Revised
    -> Approved -> Ready to Publish

Publishing (see ``publishing``) only ever acts on a task once it reaches
"ready_to_publish", and even then requires an explicit approval flag.
"""

from peacock_experts.models import EXPERT_ROLES, TASK_STATUSES, Comment, ExpertTask, VersionEntry, allowed_next_statuses
from peacock_experts.service import (
    add_comment,
    approve_task,
    assign_task,
    create_task,
    get_task,
    list_tasks,
    mark_ready_to_publish,
    request_changes,
    start_review,
    submit_revision,
)

__all__ = [
    "EXPERT_ROLES",
    "TASK_STATUSES",
    "Comment",
    "ExpertTask",
    "VersionEntry",
    "add_comment",
    "allowed_next_statuses",
    "approve_task",
    "assign_task",
    "create_task",
    "get_task",
    "list_tasks",
    "mark_ready_to_publish",
    "request_changes",
    "start_review",
    "submit_revision",
]
