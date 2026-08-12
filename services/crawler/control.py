"""Crawl control plane — pause / cancel / resume signals."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class CrawlControl:
    """In-process control flags; mirrored to DB by the persistence layer."""

    crawl_id: str
    _pause: threading.Event = field(default_factory=threading.Event)
    _cancel: threading.Event = field(default_factory=threading.Event)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self) -> None:
        # pause event clear = running; set = paused
        self._pause.clear()
        self._cancel.clear()

    def pause(self) -> None:
        with self._lock:
            self._pause.set()

    def resume(self) -> None:
        with self._lock:
            self._pause.clear()

    def cancel(self) -> None:
        with self._lock:
            self._cancel.set()
            self._pause.clear()

    @property
    def is_paused(self) -> bool:
        return self._pause.is_set() and not self._cancel.is_set()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel.is_set()

    def wait_if_paused(self, timeout: float = 0.25) -> None:
        """Block briefly while paused so the worker loop can idle safely."""
        while self.is_paused:
            self._cancel.wait(timeout=timeout)
            if self.is_cancelled:
                return
            if not self._pause.is_set():
                return
            self._pause.wait(timeout=timeout)


class CrawlControlRegistry:
    """Process-local registry of crawl controls."""

    def __init__(self) -> None:
        self._controls: dict[str, CrawlControl] = {}
        self._lock = threading.Lock()

    def get_or_create(self, crawl_id: str) -> CrawlControl:
        with self._lock:
            if crawl_id not in self._controls:
                self._controls[crawl_id] = CrawlControl(crawl_id=crawl_id)
            return self._controls[crawl_id]

    def get(self, crawl_id: str) -> CrawlControl | None:
        with self._lock:
            return self._controls.get(crawl_id)

    def drop(self, crawl_id: str) -> None:
        with self._lock:
            self._controls.pop(crawl_id, None)


CONTROL_REGISTRY = CrawlControlRegistry()
