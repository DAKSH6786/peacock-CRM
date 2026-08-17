"""Moat Data Model service models."""

from __future__ import annotations

from dataclasses import dataclass

from moat_data_model.accumulation import MoatRunResult, MoatRunSpec


@dataclass
class MoatCreateSpec:
    website_id: str
    name: str
    run: MoatRunSpec
    notes: str | None = None


@dataclass
class MoatReport:
    run_id: str
    name: str
    client_brand: str
    methodology: str
    result: MoatRunResult
