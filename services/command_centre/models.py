"""Command Centre service models."""

from __future__ import annotations

from dataclasses import dataclass

from command_centre.assembly import CommandCentreResult, CommandCentreSpec


@dataclass
class CommandCentreCreateSpec:
    website_id: str
    name: str
    centre: CommandCentreSpec
    notes: str | None = None


@dataclass
class CommandCentreReport:
    snapshot_id: str
    name: str
    client_brand: str
    methodology: str
    result: CommandCentreResult
