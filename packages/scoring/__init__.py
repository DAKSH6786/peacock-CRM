"""Deterministic scoring helpers (no LLM calls)."""

def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def weighted_score(impact: float, confidence: float, effort: float) -> float:
    """Explainable priority score used by DECIDE stage later."""
    return clamp(impact) * clamp(confidence) * (1.0 - 0.5 * clamp(effort))
