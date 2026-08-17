"""Ports for the strategic intelligence pipeline."""

from __future__ import annotations

from typing import Any, Protocol

from intelligence.models import (
    ContextItem,
    EvidenceItem,
    PipelineState,
    RequestClassification,
    StrategicRequest,
)


class ContextProvider(Protocol):
    """Supplies candidate context fragments for intelligent selection."""

    kind: str

    def candidates(self, request: StrategicRequest, classification: RequestClassification) -> list[ContextItem]: ...


class EvidenceCollector(Protocol):
    """Collects deterministic quantitative evidence (no LLM)."""

    code: str

    def collect(self, state: PipelineState) -> list[EvidenceItem]: ...


class ResearchConnector(Protocol):
    """Fetches fresh external evidence when Layer 3 requires it."""

    name: str

    async def research(self, query: str, *, organisation_id: str) -> list[EvidenceItem]: ...


class SpecialistAgent(Protocol):
    name: str
    role: str

    async def run(self, state: PipelineState) -> Any: ...


class Clock(Protocol):
    def now_iso(self) -> str: ...
