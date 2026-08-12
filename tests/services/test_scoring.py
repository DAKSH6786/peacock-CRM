from __future__ import annotations

from scoring import clamp, weighted_score


def test_clamp() -> None:
    assert clamp(1.5) == 1.0
    assert clamp(-1) == 0.0
    assert clamp(0.4) == 0.4


def test_weighted_score_is_explainable() -> None:
    high = weighted_score(impact=0.9, confidence=0.9, effort=0.1)
    low = weighted_score(impact=0.2, confidence=0.5, effort=0.9)
    assert high > low
