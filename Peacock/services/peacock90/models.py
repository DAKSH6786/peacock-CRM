"""Peacock 90 2.0 service models."""

from __future__ import annotations

from dataclasses import dataclass

from peacock90.optimiser import PlanSpec, RoadmapPlanResult


@dataclass
class Peacock90Spec:
    website_id: str
    name: str
    plan: PlanSpec
    notes: str | None = None


@dataclass
class Peacock90Report:
    plan_id: str
    name: str
    client_brand: str
    methodology: str
    result: RoadmapPlanResult
