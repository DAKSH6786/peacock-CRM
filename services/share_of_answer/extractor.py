"""Answer entity extraction for Share of Answer.

Derives multi-indicator readings from generative answer text.
Token span is recorded as a diagnostic only — never treated as influence alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from share_of_answer.scoring import EntityIndicatorReading

POSITIVE_CLAIM_PATTERNS = (
    r"\brecommend(?:ed|s|ing)?\b",
    r"\bbest\b",
    r"\btop(?:\s+choice|\s+pick)?\b",
    r"\bleading\b",
    r"\bstrong(?:est)?\b",
    r"\bideal\b",
    r"\bexcellent\b",
    r"\bpreferred\b",
    r"\boutperform(?:s|ed|ing)?\b",
    r"\bstands?\s+out\b",
    r"\bgo[- ]to\b",
    r"\bmarket\s+leader\b",
)

NEGATIVE_CLAIM_PATTERNS = (
    r"\bavoid\b",
    r"\bweak(?:er|est)?\b",
    r"\blimited\b",
    r"\black(?:s|ing)?\b",
    r"\bexpensive\b",
    r"\boverpriced\b",
    r"\brisky\b",
    r"\bnot\s+(?:ideal|recommended|suitable)\b",
    r"\bdrawback(?:s)?\b",
    r"\bconcern(?:s)?\b",
    r"\bnarrow\b",
    r"\bniche\s+only\b",
)

NEUTRAL_CLAIM_PATTERNS = (
    r"\balternative\b",
    r"\boption\b",
    r"\bincludes?\b",
    r"\balso\b",
    r"\bconsider\b",
    r"\bmight\b",
    r"\bcan\s+be\b",
    r"\bsuitable\s+for\b",
    r"\bappears?\b",
)

RECOMMENDATION_PATTERNS = (
    r"\b(?:strongly\s+)?recommend(?:ed|s|ing)?\b",
    r"\bbest\s+(?:overall|choice|option|pick|for)\b",
    r"\btop\s+(?:pick|choice|recommendation)\b",
    r"\bprefer(?:red|s|able)?\b",
    r"\bshould\s+(?:choose|pick|select|use)\b",
    r"\bgo\s+with\b",
    r"\bclear\s+winner\b",
    r"\bnumber\s+one\b",
    r"\b#1\b",
)

CITATION_PATTERNS = (
    r"https?://[^\s)>\]]+",
    r"\baccording\s+to\b",
    r"\bcited?\b",
    r"\bsource(?:s)?\b",
    r"\breport(?:s|ed)?\b",
    r"\bstudy\b",
    r"\bdocumentation\b",
    r"\[\d+\]",
)

WIN_PATTERNS = (
    r"\bbetter\s+than\b",
    r"\bahead\s+of\b",
    r"\boutperform(?:s|ed|ing)?\b",
    r"\bwins?\b",
    r"\bleads?\b",
    r"\bsurpass(?:es|ed|ing)?\b",
)

LOSE_PATTERNS = (
    r"\bbehind\b",
    r"\btrails?\b",
    r"\blags?\b",
    r"\bweaker\s+than\b",
    r"\bloss(?:es|ing)?\b",
    r"\bfalls?\s+short\b",
)

TIE_PATTERNS = (
    r"\btie\b",
    r"\bon\s+par\b",
    r"\bsimilar(?:ly)?\b",
    r"\bcomparable\b",
    r"\bneck\s+and\s+neck\b",
    r"\bequally\b",
)


@dataclass(frozen=True)
class AnswerDocument:
    prompt_text: str
    engine_code: str
    raw_excerpt: str
    model_code: str | None = None
    answer_token_count: int | None = None


def _approx_token_count(text: str) -> int:
    return max(1, len(re.findall(r"\S+", text)))


def _compile_many(patterns: tuple[str, ...]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_POS = _compile_many(POSITIVE_CLAIM_PATTERNS)
_NEG = _compile_many(NEGATIVE_CLAIM_PATTERNS)
_NEU = _compile_many(NEUTRAL_CLAIM_PATTERNS)
_REC = _compile_many(RECOMMENDATION_PATTERNS)
_CIT = _compile_many(CITATION_PATTERNS)
_WIN = _compile_many(WIN_PATTERNS)
_LOSE = _compile_many(LOSE_PATTERNS)
_TIE = _compile_many(TIE_PATTERNS)


def _entity_pattern(name: str) -> re.Pattern[str]:
    escaped = re.escape(name.strip())
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _count_matches(patterns: list[re.Pattern[str]], text: str) -> int:
    return sum(1 for p in patterns if p.search(text))


def _mention_spans(text: str, name: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in _entity_pattern(name).finditer(text)]


def _sentence_windows(sentences: list[str], name: str) -> list[str]:
    """Only sentences that mention the entity — avoids cross-brand bleed."""
    return [s for s in sentences if _entity_pattern(name).search(s)]


def _ordered_list_rank(text: str, name: str) -> int | None:
    """Detect numbered / bulleted list order for the entity."""
    lines = text.splitlines()
    ranked: list[str] = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(\d+[\.\)]\s+|[-*•]\s+)", stripped):
            ranked.append(stripped)
    if not ranked:
        # Also split on "1) ... 2) ..." inline
        inline = re.findall(
            r"(?:^|\s)(\d+[\.\)])\s+([^0-9]+?)(?=(?:\s+\d+[\.\)])|$)",
            text,
        )
        ranked = [f"{num} {body}".strip() for num, body in inline]
    for idx, item in enumerate(ranked):
        if _entity_pattern(name).search(item):
            return idx + 1
    return None


def _first_appearance_rank(entities: list[str], text: str) -> dict[str, int]:
    first_pos: dict[str, int] = {}
    for name in entities:
        spans = _mention_spans(text, name)
        if spans:
            first_pos[name] = spans[0][0]
    ordered = sorted(first_pos.items(), key=lambda kv: kv[1])
    return {name: idx + 1 for idx, (name, _) in enumerate(ordered)}


def _claim_counts(windows: list[str]) -> tuple[int, int, int]:
    pos = neg = neu = 0
    for window in windows:
        pos += _count_matches(_POS, window)
        neg += _count_matches(_NEG, window)
        neu += _count_matches(_NEU, window)
    return pos, neg, neu


def _recommendation_strength(windows: list[str], position: int | None) -> float:
    if not windows:
        return 0.0
    hits = sum(_count_matches(_REC, w) for w in windows)
    base = min(1.0, 0.25 * hits)
    if position == 1:
        base = min(1.0, base + 0.35)
    elif position == 2:
        base = min(1.0, base + 0.18)
    elif position is not None and position <= 3:
        base = min(1.0, base + 0.08)
    # Soft floor when mentioned with positive language
    if hits == 0 and position is not None:
        base = max(base, max(0.1, 0.55 - 0.1 * (position - 1)))
    return round(min(1.0, base), 4)


def _answer_space(sentences: list[str], name: str) -> float:
    if not sentences:
        return 0.0
    hits = sum(1 for s in sentences if _entity_pattern(name).search(s))
    return round(min(1.0, hits / len(sentences)), 4)


def _citation_ownership(windows: list[str], text: str, name: str) -> float:
    if not windows:
        return 0.0
    near = sum(_count_matches(_CIT, w) for w in windows)
    # Domain-ish ownership: brand token inside a URL
    slug = re.sub(r"[^a-z0-9]+", "", name.lower())
    url_hits = 0
    if slug:
        for m in re.finditer(r"https?://[^\s)>\]]+", text, re.IGNORECASE):
            if slug in m.group(0).lower():
                url_hits += 1
    score = min(1.0, 0.2 * near + 0.35 * url_hits)
    return round(score, 4)


def _semantic_prominence(
    *,
    mention_count: int,
    position: int | None,
    answer_space: float,
    first_char: int | None,
    text_len: int,
) -> float:
    if mention_count <= 0:
        return 0.0
    freq = min(1.0, mention_count / 5.0)
    early = 0.0
    if first_char is not None and text_len > 0:
        early = max(0.0, 1.0 - (first_char / text_len))
    rank_boost = 0.0
    if position == 1:
        rank_boost = 0.25
    elif position == 2:
        rank_boost = 0.12
    score = 0.35 * freq + 0.3 * early + 0.2 * answer_space + rank_boost
    return round(min(1.0, score), 4)


def _comparison_outcome(
    windows: list[str],
    *,
    position: int | None,
    mentioned: bool,
    entity_count_mentioned: int,
) -> str:
    if not mentioned:
        return "absent"
    joined = " ".join(windows)
    wins = _count_matches(_WIN, joined)
    losses = _count_matches(_LOSE, joined)
    ties = _count_matches(_TIE, joined)
    if wins > losses and wins > 0:
        return "win"
    if losses > wins and losses > 0:
        return "lose"
    if ties > 0 and wins == losses:
        return "tie"
    if wins and losses:
        return "mixed"
    if position == 1 and entity_count_mentioned >= 2:
        return "win"
    if position is not None and position >= 3 and entity_count_mentioned >= 3:
        return "lose"
    if position == 2:
        return "tie"
    return "mixed" if entity_count_mentioned >= 2 else "absent"


def extract_entity_indicators(
    document: AnswerDocument,
    *,
    client_brand: str,
    competitor_brands: list[str],
) -> list[EntityIndicatorReading]:
    """Extract multi-indicator readings for client + competitors from an answer."""
    entities = [client_brand, *competitor_brands]
    seen: set[str] = set()
    ordered: list[str] = []
    for name in entities:
        key = name.strip()
        if not key or key.lower() in seen:
            continue
        seen.add(key.lower())
        ordered.append(key)

    text = document.raw_excerpt or ""
    sentences = _sentences(text)
    total_tokens = document.answer_token_count or _approx_token_count(text)
    appearance_rank = _first_appearance_rank(ordered, text)

    # Collect per-entity span stats first
    spans_by_name: dict[str, list[tuple[int, int]]] = {
        name: _mention_spans(text, name) for name in ordered
    }
    mentioned_names = [n for n, spans in spans_by_name.items() if spans]

    readings: list[EntityIndicatorReading] = []
    token_spans: dict[str, float] = {}

    for name in ordered:
        spans = spans_by_name[name]
        mentioned = bool(spans)
        mention_count = len(spans)

        list_rank = _ordered_list_rank(text, name) if mentioned else None
        position = list_rank or appearance_rank.get(name)
        windows = _sentence_windows(sentences, name) if mentioned else []

        pos_c, neg_c, neu_c = _claim_counts(windows) if mentioned else (0, 0, 0)
        answer_space = _answer_space(sentences, name) if mentioned else 0.0
        recommendation = (
            _recommendation_strength(windows, position) if mentioned else 0.0
        )
        citation = _citation_ownership(windows, text, name) if mentioned else 0.0
        first_char = spans[0][0] if spans else None
        semantic = (
            _semantic_prominence(
                mention_count=mention_count,
                position=position,
                answer_space=answer_space,
                first_char=first_char,
                text_len=max(1, len(text)),
            )
            if mentioned
            else 0.0
        )
        outcome = _comparison_outcome(
            windows,
            position=position,
            mentioned=mentioned,
            entity_count_mentioned=len(mentioned_names),
        )

        # Diagnostic token span: tokens in entity sentences / answer tokens
        if mentioned:
            covered = sum(len(re.findall(r"\S+", w)) for w in windows)
            token_spans[name] = covered / max(1, total_tokens)
        else:
            token_spans[name] = 0.0

        readings.append(
            EntityIndicatorReading(
                entity_name=name,
                is_client=name.lower() == client_brand.lower(),
                mention=mentioned,
                mention_count=mention_count,
                position=position if mentioned else None,
                recommendation_strength=recommendation,
                answer_space=answer_space,
                citation_ownership=citation,
                semantic_prominence=semantic,
                positive_claims=pos_c,
                negative_claims=neg_c,
                neutral_claims=neu_c,
                comparison_outcome=outcome,
                token_span_ratio=min(1.0, token_spans[name]),
            )
        )

    # Renormalise diagnostic token spans among mentioned entities
    mentioned_readings = [r for r in readings if r.mention]
    span_sum = sum(r.token_span_ratio for r in mentioned_readings)
    if span_sum > 0:
        normalised: list[EntityIndicatorReading] = []
        for r in readings:
            if r.mention:
                normalised.append(
                    EntityIndicatorReading(
                        entity_name=r.entity_name,
                        is_client=r.is_client,
                        mention=r.mention,
                        mention_count=r.mention_count,
                        position=r.position,
                        recommendation_strength=r.recommendation_strength,
                        answer_space=r.answer_space,
                        citation_ownership=r.citation_ownership,
                        semantic_prominence=r.semantic_prominence,
                        positive_claims=r.positive_claims,
                        negative_claims=r.negative_claims,
                        neutral_claims=r.neutral_claims,
                        comparison_outcome=r.comparison_outcome,
                        token_span_ratio=r.token_span_ratio / span_sum,
                    )
                )
            else:
                normalised.append(r)
        return normalised

    return readings
