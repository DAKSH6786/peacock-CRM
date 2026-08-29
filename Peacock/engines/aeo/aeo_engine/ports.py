"""Ports (interfaces) for aeo_engine. External deps must be adapted, not called directly."""

from typing import Protocol


class Clock(Protocol):
    def now_iso(self) -> str: ...
