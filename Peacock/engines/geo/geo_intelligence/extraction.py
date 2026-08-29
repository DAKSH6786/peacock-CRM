"""Deterministic keyword/entity/citation extraction from collected LLM responses.

No provider SDK, no external NLP dependency — only stdlib regex/Counter
heuristics, so this layer works identically regardless of which AI plugins
produced the text (or whether the text is a simulated fallback).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from citation_graph.classify import classify_source, extract_urls, host_from_url

from geo_intelligence.models import (
    CitationSignal,
    EntityMention,
    GeoExtractionResult,
    KeywordSignal,
    ProviderResponse,
    QuestionSignal,
    TerminologyProfile,
    TopicSignal,
)

_STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or but if then else for nor so yet both either neither not
    is are was were be been being do does did doing have has had having
    i you he she it we they me him her us them my your his its our their
    this that these those there here as of to in on at by from with without
    into onto over under again further once more most other some such no
    only own same too very can will just should would could may might must
    about above after before between during through above below up down
    out off than also than because while when where why how what which who
    whom all any each few more most other some such nor own same so than too
    very s t can will just don now
    """.split()
)

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]{1,}")
_URL_RE = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_QUESTION_RE = re.compile(
    r"\b(what|why|how|when|where|who|which|can|does|is|are|should|will|do)\b.+\?",
    re.IGNORECASE,
)
_TITLECASE_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b")
_SENTENCE_STARTER_BLOCKLIST = frozenset(
    {
        "the",
        "this",
        "that",
        "these",
        "those",
        "however",
        "also",
        "in",
        "on",
        "at",
        "it",
        "if",
        "as",
        "for",
        "but",
        "and",
        "so",
        "we",
        "you",
        "they",
        "overall",
        "additionally",
        "furthermore",
        "recommended",
        "sources",
        "what",
        "how",
        "which",
        "why",
        "when",
        "where",
        "who",
        "does",
        "is",
        "are",
        "should",
        "will",
        "can",
        "do",
        "see",
        "related",
        "because",
        "reference",
    }
)


def _strip_urls(text: str) -> str:
    return _URL_RE.sub(" ", text or "")


def tokenize(text: str) -> list[str]:
    words = [w.lower() for w in _WORD_RE.findall(_strip_urls(text))]
    return [w for w in words if len(w) > 2 and w not in _STOPWORDS]


def top_ngrams(text: str, *, sizes: tuple[int, ...] = (1, 2, 3), top_k: int = 15) -> list[tuple[str, int]]:
    tokens = tokenize(text)
    counter: Counter[str] = Counter()
    for size in sizes:
        for i in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[i : i + size])
            counter[phrase] += 1
    return counter.most_common(top_k)


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text or "") if s.strip()]


def extract_questions(text: str) -> list[str]:
    questions: list[str] = []
    for sentence in split_sentences(text):
        if sentence.endswith("?") or _QUESTION_RE.search(sentence):
            questions.append(sentence)
    return questions


def extract_title_case_entities(text: str) -> list[str]:
    """Heuristic named-entity spotting — capitalised word sequences, minus common false positives."""
    candidates = [m.strip() for m in _TITLECASE_RE.findall(text or "") if m.strip()]
    found: list[str] = []
    for candidate in candidates:
        words = candidate.split()
        if not words:
            continue
        first_lower = words[0].lower()
        if len(words) == 1 and (first_lower in _SENTENCE_STARTER_BLOCKLIST or len(words[0]) < 3):
            continue
        found.append(candidate)
    return found


def extract_citations(text: str, engine_code: str, *, client_domains: list[str], competitor_domains: list[str]) -> list[CitationSignal]:
    signals: list[CitationSignal] = []
    for url in extract_urls(text or ""):
        domain = host_from_url(url)
        source_class, _is_comp, _is_client, _authority = classify_source(
            url=url,
            domain=domain,
            competitor_domains=competitor_domains,
            client_domains=client_domains,
        )
        signals.append(
            CitationSignal(url=url, domain=domain, source_class=source_class, engine_code=engine_code)
        )
    return signals


def extract_geo_intelligence(
    *,
    client_brand: str,
    competitors: list[str],
    site_topics: list[str],
    responses: list[ProviderResponse],
    client_domains: list[str] | None = None,
    competitor_domains: list[str] | None = None,
) -> GeoExtractionResult:
    client_domains = client_domains or []
    competitor_domains = competitor_domains or []

    keyword_counter: Counter[str] = Counter()
    keyword_engines: dict[str, set[str]] = defaultdict(set)
    entity_counter: Counter[str] = Counter()
    entity_engines: dict[str, set[str]] = defaultdict(set)
    questions: list[QuestionSignal] = []
    citations: list[CitationSignal] = []
    terminology_by_engine: list[TerminologyProfile] = []
    topic_counter: Counter[tuple[str, str]] = Counter()

    known_brands = {client_brand.strip().lower(): "client"}
    for competitor in competitors:
        if competitor.strip():
            known_brands[competitor.strip().lower()] = "competitor"

    for response in responses:
        text = response.content or ""
        if not text.strip():
            terminology_by_engine.append(
                TerminologyProfile(engine_code=response.engine_code, engine_name=response.engine_name, top_terms=[])
            )
            continue

        ngrams = top_ngrams(text, top_k=20)
        for phrase, freq in ngrams:
            keyword_counter[phrase] += freq
            keyword_engines[phrase].add(response.engine_code)

        # Terminology should highlight distinctive phrasing, not just repeat the brand name.
        top_terms = [
            phrase
            for phrase, _freq in ngrams
            if len(phrase.split()) <= 2 and phrase not in known_brands
        ]
        terminology_by_engine.append(
            TerminologyProfile(engine_code=response.engine_code, engine_name=response.engine_name, top_terms=top_terms[:6])
        )

        for question in extract_questions(text):
            questions.append(QuestionSignal(question=question, engine_code=response.engine_code))

        citations.extend(
            extract_citations(
                text,
                response.engine_code,
                client_domains=client_domains,
                competitor_domains=competitor_domains,
            )
        )

        lower_text = text.lower()
        for brand_name, kind in known_brands.items():
            if brand_name and brand_name in lower_text:
                entity_counter[brand_name] += lower_text.count(brand_name)
                entity_engines[brand_name].add(response.engine_code)

        for candidate in extract_title_case_entities(text):
            key = candidate.lower()
            if key in known_brands:
                continue  # already counted with canonical casing above
            entity_counter[candidate] += 1
            entity_engines[candidate].add(response.engine_code)

        # Topics associated with top-ranked/recommended brands: co-occurrence within
        # sentences that both mention a known brand and carry recommendation language.
        recommend_re = re.compile(r"\b(recommend|best|top|leading|popular|trusted|great choice)\b", re.IGNORECASE)
        for sentence in split_sentences(text):
            sentence_lower = sentence.lower()
            mentioned_brand = next((b for b in known_brands if b and b in sentence_lower), None)
            if mentioned_brand and recommend_re.search(sentence_lower):
                for phrase, _freq in top_ngrams(sentence, sizes=(2, 3), top_k=6):
                    if phrase != mentioned_brand:
                        topic_counter[(phrase, mentioned_brand)] += 1

    entities: list[EntityMention] = []
    for name, count in entity_counter.most_common(30):
        canonical = client_brand if name == client_brand.strip().lower() else name
        kind = known_brands.get(name, "other")
        entities.append(
            EntityMention(name=canonical, kind=kind, frequency=count, engine_codes=sorted(entity_engines[name]))
        )
    entities.sort(key=lambda e: e.frequency, reverse=True)

    competitor_mentions = [e for e in entities if e.kind == "competitor"]

    keywords = [
        KeywordSignal(phrase=phrase, frequency=freq, engine_codes=sorted(keyword_engines[phrase]))
        for phrase, freq in keyword_counter.most_common(25)
    ]

    top_brand_topics = [
        TopicSignal(topic=phrase, associated_entity=brand, frequency=freq)
        for (phrase, brand), freq in topic_counter.most_common(10)
    ]

    site_topics_blob = " | ".join(t.lower() for t in site_topics)
    missing_topics: list[str] = []
    for phrase, _freq in keyword_counter.most_common(40):
        if len(phrase.split()) < 2:
            continue  # single words are too generic to call a "missing topic"
        if phrase in site_topics_blob:
            continue
        missing_topics.append(phrase)
        if len(missing_topics) >= 8:
            break

    return GeoExtractionResult(
        keywords=keywords,
        entities=entities[:20],
        questions=questions[:20],
        citations=citations[:20],
        competitor_mentions=competitor_mentions[:10],
        terminology_by_engine=terminology_by_engine,
        top_brand_topics=top_brand_topics,
        missing_topics=missing_topics,
    )
