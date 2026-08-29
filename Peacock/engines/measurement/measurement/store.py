"""In-memory snapshot store.

Peacock One runs statelessly by default (no database is required for the
dashboard or Site Intelligence engine). This store keeps the process-local
history needed for before/after measurement and decay detection; it resets
on restart unless/until a persistent connector is configured. That limit is
surfaced explicitly rather than hidden.
"""

from __future__ import annotations

from collections import defaultdict

from measurement.models import Snapshot

_STORE: dict[str, list[Snapshot]] = defaultdict(list)
MAX_SNAPSHOTS_PER_URL = 50


def save_snapshot(snapshot: Snapshot) -> None:
    history = _STORE[snapshot.url]
    history.append(snapshot)
    history.sort(key=lambda s: s.captured_at)
    if len(history) > MAX_SNAPSHOTS_PER_URL:
        del history[: len(history) - MAX_SNAPSHOTS_PER_URL]


def get_history(url: str) -> list[Snapshot]:
    return list(_STORE.get(url, []))


def latest(url: str) -> Snapshot | None:
    history = _STORE.get(url)
    return history[-1] if history else None


def clear_all() -> None:
    """Test/dev helper — never called from production request handling."""
    _STORE.clear()
