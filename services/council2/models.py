"""Peacock Council 2.0 service models."""

from __future__ import annotations

from dataclasses import dataclass

from council2.debate import CouncilBrief, CouncilDebateResult


@dataclass
class Council2Spec:
    website_id: str
    name: str
    brief: CouncilBrief
    notes: str | None = None


@dataclass
class Council2Report:
    session_id: str
    name: str
    client_brand: str
    methodology: str
    result: CouncilDebateResult
