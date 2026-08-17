"""AI Connector Security service models."""

from __future__ import annotations

from dataclasses import dataclass

from ai_connector_security.engine import SecurityScanResult, SecurityScanSpec


@dataclass
class AiConnectorSecurityCreateSpec:
    website_id: str
    name: str
    scan: SecurityScanSpec
    notes: str | None = None


@dataclass
class AiConnectorSecurityReport:
    scan_id: str
    name: str
    client_brand: str
    methodology: str
    result: SecurityScanResult
