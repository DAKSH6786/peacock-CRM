from __future__ import annotations

from scoring import clamp, peacock_seo_score, weighted_score, ScoreResult, PEACOCK_SEO_WEIGHTS


def test_clamp() -> None:
    assert clamp(1.5) == 1.0
    assert clamp(-1) == 0.0
    assert clamp(0.4) == 0.4


def test_weighted_score_is_explainable() -> None:
    high = weighted_score(impact=0.9, confidence=0.9, effort=0.1)
    low = weighted_score(impact=0.2, confidence=0.5, effort=0.9)
    assert high > low


def test_peacock_weights_sum_to_one() -> None:
    assert abs(sum(PEACOCK_SEO_WEIGHTS.values()) - 1.0) < 1e-9


def test_missing_section_reduces_confidence() -> None:
    partial = {
        "technical_seo": ScoreResult("technical_seo", "Technical SEO", 90, 1.0),
    }
    score = peacock_seo_score(partial)
    assert score.score > 0
    assert score.confidence < 1.0
