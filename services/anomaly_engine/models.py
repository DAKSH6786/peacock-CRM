"""Anomaly Engine service models."""

from __future__ import annotations

from dataclasses import dataclass

from anomaly_engine.detection import AnomalyScanResult, AnomalyScanSpec


@dataclass
class AnomalyEngineSpec:
    website_id: str
    name: str
    scan: AnomalyScanSpec
    notes: str | None = None


@dataclass
class AnomalyEngineReport:
    scan_id: str
    name: str
    client_brand: str
    methodology: str
    result: AnomalyScanResult
