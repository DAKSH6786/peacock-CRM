"""Peacock Opportunity Engine service models."""

from __future__ import annotations

from dataclasses import dataclass, field

from opportunity_engine.ranking import (
    OutcomeFeedbackInput,
    ScanResult,
    SignalInput,
)


@dataclass
class OpportunityScanSpec:
    website_id: str
    name: str
    client_brand: str
    signals: list[SignalInput]
    outcome_feedback: list[OutcomeFeedbackInput] = field(default_factory=list)
    notes: str | None = None


@dataclass
class OpportunityScanReport:
    scan_id: str
    name: str
    client_brand: str
    methodology: str
    always_on_layer: bool
    result: ScanResult
