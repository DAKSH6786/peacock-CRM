"""Information Gain Engine — does this page add anything competitors don't already say?

Signals are detected with regex/pattern matching over the page's REAL crawled
body text (never invented). The scoring math reuses
``content_lab.scoring.compute_information_gain`` — the same deterministic
formula already used for proposed-content evaluation — fed with penalty/
reward *strengths* derived from what is literally present on the page.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from content_lab.scoring import InfoGainSignalResult, compute_information_gain

from crawler.extract import near_duplicate

_REWARD_PATTERNS: dict[str, re.Pattern[str]] = {
    "original_data": re.compile(
        r"\b(our (data|survey|research)|proprietary data|we surveyed|n\s*=\s*\d+|based on \d+[\s,]*(responses|customers|users))\b",
        re.IGNORECASE,
    ),
    "original_experiment": re.compile(
        r"\b(we (tested|ran an? (experiment|a/?b test))|our experiment|controlled experiment)\b", re.IGNORECASE
    ),
    "new_comparison": re.compile(r"\b(vs\.?|versus|compared to|head-to-head|comparison table)\b", re.IGNORECASE),
    "expert_opinion": re.compile(
        r"\b(according to (our|the) (ceo|founder|cto|expert|dr\.|professor)|interview with|quoted?\s+[A-Z][a-z]+)\b",
        re.IGNORECASE,
    ),
    "first_party_insight": re.compile(
        r"\b(from our (customers|users|clients)|internal data|our own experience|in our experience)\b", re.IGNORECASE
    ),
    "unique_framework": re.compile(r"\b(our framework|our methodology|our approach|playbook we)\b", re.IGNORECASE),
    "new_synthesis": re.compile(r"\b(we (combined|analysed|analyzed|synthesi[sz]ed))\b", re.IGNORECASE),
    "fresh_statistics": re.compile(r"\b(20(2[4-9]|3[0-9]))\b"),
    "novel_example": re.compile(r"\b(case study|real[- ]world example|worked example|walkthrough)\b", re.IGNORECASE),
}

_PENALTY_PATTERNS: dict[str, re.Pattern[str]] = {
    "generic_duplication": re.compile(
        r"\b(ultimate guide|everything you need to know|complete guide|beginner'?s guide|101\b)\b", re.IGNORECASE
    ),
    "common_definitions": re.compile(r"\b(what is [a-z]|is defined as|refers to the)\b", re.IGNORECASE),
    "commodity_advice": re.compile(r"\b(tips and tricks|best practices|top \d+ tips)\b", re.IGNORECASE),
}

_STATISTIC_RE = re.compile(r"\b\d+(\.\d+)?\s?%|\b\d{2,}(,\d{3})*\b")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def detect_information_gain_signals(
    text: str, *, competitor_text: str | None = None
) -> tuple[dict[str, float], dict[str, float], list[str]]:
    """Pattern-match REAL page text for information-gain penalty/reward signals.

    Returns (penalties, rewards, evidence_notes). ``near_identical_competitor_coverage``
    is only ever populated when ``competitor_text`` is supplied — otherwise it is
    omitted rather than guessed.
    """
    blob = text or ""
    rewards: dict[str, float] = {}
    penalties: dict[str, float] = {}
    evidence: list[str] = []

    for code, pattern in _REWARD_PATTERNS.items():
        matches = pattern.findall(blob)
        if matches:
            strength = _clamp01(0.4 + 0.15 * min(len(matches), 4))
            rewards[code] = strength
            evidence.append(f"Reward signal '{code.replace('_', ' ')}' matched {len(matches)}× in page text.")

    for code, pattern in _PENALTY_PATTERNS.items():
        matches = pattern.findall(blob)
        if matches:
            strength = _clamp01(0.35 + 0.15 * min(len(matches), 4))
            penalties[code] = strength
            evidence.append(f"Penalty signal '{code.replace('_', ' ')}' matched {len(matches)}× in page text.")

    stat_count = len(_STATISTIC_RE.findall(blob))
    if stat_count >= 3 and "original_data" not in rewards:
        rewards["original_data"] = _clamp01(0.3 + 0.05 * min(stat_count, 10))
        evidence.append(f"Detected {stat_count} numeric statistic(s) in page text.")

    if competitor_text:
        similarity = 1.0 if not blob or not competitor_text else None
        try:
            is_near_dup = near_duplicate(blob, competitor_text, threshold=0.55)
        except Exception:  # noqa: BLE001 — never let a heuristic crash the report
            is_near_dup = False
        if is_near_dup:
            penalties["near_identical_competitor_coverage"] = 0.7
            evidence.append("Page text is textually similar to the supplied competitor page (token overlap ≥ 55%).")

    if not evidence:
        evidence.append("No strong original-research or generic-duplication patterns detected in page text.")

    return penalties, rewards, evidence


def score_information_gain(
    text: str, *, competitor_text: str | None = None
) -> tuple[float, list[InfoGainSignalResult], list[str]]:
    """Real Information Gain Score (0-100) for one crawled page's text."""
    penalties, rewards, evidence = detect_information_gain_signals(text, competitor_text=competitor_text)
    score, signals = compute_information_gain(penalties=penalties, rewards=rewards)
    return score, signals, evidence


def freshness_signal(text: str) -> tuple[str, str]:
    """Best-effort freshness read from in-page year mentions — a proxy, not a CMS-verified date."""
    years = sorted({int(y) for y in re.findall(r"\b(20\d{2})\b", text or "")})
    if not years:
        return "unknown", "No 4-digit year mentioned in page text — publish/update date not verifiable from crawl."
    current_year = datetime.now(tz=UTC).year
    latest = years[-1]
    if latest >= current_year - 1:
        return "fresh", f"Most recent year mentioned in page text is {latest}."
    if latest >= current_year - 3:
        return "aging", f"Most recent year mentioned in page text is {latest} ({current_year - latest} year(s) old)."
    return "stale", f"Most recent year mentioned in page text is {latest} ({current_year - latest} year(s) old)."
