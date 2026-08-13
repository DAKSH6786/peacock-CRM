"""Ask Peacock 2.0 service models."""

from __future__ import annotations

from dataclasses import dataclass

from ask_peacock.analysis import AskSessionResult, AskSessionSpec


@dataclass
class AskPeacockSpec:
    website_id: str
    name: str
    session: AskSessionSpec
    notes: str | None = None


@dataclass
class AskPeacockReport:
    session_id: str
    name: str
    client_brand: str
    methodology: str
    result: AskSessionResult
