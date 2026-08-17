"""Peacock Action Engine service models."""

from __future__ import annotations

from dataclasses import dataclass

from action_engine.workflow import ActionDraft, ActionView


@dataclass
class ActionEngineSpec:
    website_id: str
    draft: ActionDraft
    granted_permissions: list[str] | None = None


@dataclass
class ActionEngineReport:
    action_id: str
    methodology: str
    view: ActionView
