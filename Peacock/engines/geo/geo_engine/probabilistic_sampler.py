"""Rate-limited controlled probe execution — never abusive API traffic."""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from geo_engine.probabilistic_models import (
    HARD_MAX_REPETITIONS,
    ProbeCellSpec,
    ProbeOutcome,
    RateLimitPolicy,
)


ProbeFn = Callable[[ProbeCellSpec, int], Awaitable[ProbeOutcome]]


@dataclass
class RateLimiter:
    """Token-ish limiter: min interval + calls/minute + concurrency + total cap."""

    policy: RateLimitPolicy
    _timestamps: list[float]
    _total_calls: int
    _lock: asyncio.Lock

    def __init__(self, policy: RateLimitPolicy) -> None:
        self.policy = policy.clamped()
        self._timestamps = []
        self._total_calls = 0
        self._lock = asyncio.Lock()
        self._last_call_at = 0.0
        self._inflight = 0

    @property
    def total_calls(self) -> int:
        return self._total_calls

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                if self._total_calls >= self.policy.max_total_calls:
                    raise RuntimeError(
                        f"Campaign call cap reached ({self.policy.max_total_calls}). "
                        "Uncontrolled traffic is forbidden."
                    )
                if self._inflight >= self.policy.max_concurrent:
                    wait = 0.05
                else:
                    # prune window
                    window_start = now - 60.0
                    self._timestamps = [t for t in self._timestamps if t >= window_start]
                    if len(self._timestamps) >= self.policy.max_calls_per_minute:
                        wait = max(0.05, 60.0 - (now - self._timestamps[0]))
                    else:
                        since_last = (now - self._last_call_at) * 1000.0
                        if since_last < self.policy.min_interval_ms:
                            wait = (self.policy.min_interval_ms - since_last) / 1000.0
                        else:
                            self._inflight += 1
                            self._last_call_at = now
                            self._timestamps.append(now)
                            self._total_calls += 1
                            return
            await asyncio.sleep(wait)

    async def release(self) -> None:
        async with self._lock:
            self._inflight = max(0, self._inflight - 1)


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_repetitions(requested: int, *, max_repetitions: int) -> int:
    if requested < 1:
        raise ValueError("target_repetitions must be >= 1")
    if requested > HARD_MAX_REPETITIONS:
        raise ValueError(
            f"target_repetitions={requested} exceeds hard ceiling {HARD_MAX_REPETITIONS}. "
            "Peacock One forbids abusive sampling volume."
        )
    return min(requested, max_repetitions, HARD_MAX_REPETITIONS)


async def run_controlled_repetitions(
    *,
    cell: ProbeCellSpec,
    repetitions: int,
    rate_limiter: RateLimiter,
    probe_fn: ProbeFn,
) -> list[ProbeOutcome]:
    """Execute N controlled repetitions under the rate limiter."""
    n = validate_repetitions(
        repetitions, max_repetitions=rate_limiter.policy.max_repetitions
    )
    outcomes: list[ProbeOutcome] = []
    for run_index in range(1, n + 1):
        await rate_limiter.acquire()
        try:
            outcome = await probe_fn(cell, run_index)
            outcomes.append(outcome)
        finally:
            await rate_limiter.release()
    return outcomes


async def mock_visibility_probe(cell: ProbeCellSpec, run_index: int) -> ProbeOutcome:
    """Deterministic-ish mock probe for tests — varies by run_index (probabilistic).

    Not a live engine call. Used so the stack never needs uncontrolled traffic.
    """
    seed = (
        sum(ord(c) for c in cell.prompt_text)
        + sum(ord(c) for c in cell.engine_code)
        + run_index * 17
    )
    brand_mentioned = (seed % 10) < 7  # ~0.7
    brand_cited = (seed % 10) < 3  # ~0.3
    brand_top3 = brand_mentioned and (seed % 10) < 5  # ~0.5 of mentioned-ish
    position = (seed % 5) + 1 if brand_mentioned else None
    competitors = []
    if (seed % 10) < 8:
        competitors.append("competitor_a")
    if (seed % 10) < 6:
        competitors.append("competitor_b")
    return ProbeOutcome(
        brand_mentioned=brand_mentioned,
        brand_cited=brand_cited,
        brand_top3=bool(brand_top3),
        brand_position=position,
        competitor_mentions=competitors,
        raw_excerpt=f"[mock {cell.engine_code} run {run_index}]",
        structured_summary=f"mock mention={brand_mentioned} cite={brand_cited}",
    )
