"""Source classification heuristics for citation domains/URLs."""

from __future__ import annotations

import re

from citation_graph.scoring import normalise_domain

# Authority priors by source class (explainable, not secret)
AUTHORITY_PRIOR: dict[str, float] = {
    "government": 0.92,
    "academic": 0.9,
    "industry_publication": 0.78,
    "news": 0.72,
    "review": 0.65,
    "independent": 0.55,
    "forum": 0.4,
    "competitor_owned": 0.45,
    "unknown": 0.5,
}

_GOV = re.compile(r"\.(gov|gob|gouv)(\.[a-z]{2})?$|\.mil$", re.I)
_ACADEMIC = re.compile(r"\.edu$|\.ac\.[a-z]{2}$|arxiv\.org|pubmed\.ncbi|scholar\.google", re.I)
_NEWS = re.compile(
    r"(reuters|bloomberg|nytimes|wsj|ft\.com|forbes|techcrunch|theverge|"
    r"wired|cnn|bbc\.|guardian|washingtonpost|businessinsider)",
    re.I,
)
_FORUM = re.compile(
    r"(reddit\.com|quora\.com|stackexchange|stackoverflow|discourse|forum)",
    re.I,
)
_REVIEW = re.compile(
    r"(g2\.com|capterra|trustpilot|gartner|forrester|trustradius|sitejabber|"
    r"consumeraffairs|yelp\.com)",
    re.I,
)
_INDUSTRY = re.compile(
    r"(wikipedia\.org|investopedia|harvard\.edu|mckinsey|gartner|"
    r"hbr\.org|mit\.edu|stanford\.edu)",
    re.I,
)


def classify_source(
    *,
    url: str,
    domain: str | None = None,
    competitor_domains: list[str] | None = None,
    client_domains: list[str] | None = None,
) -> tuple[str, bool, bool, float]:
    """Return (source_class, is_competitor_owned, is_client_owned, authority_proxy)."""
    host = normalise_domain(domain or url)
    full = url or host
    competitor_domains = [normalise_domain(d) for d in (competitor_domains or []) if d]
    client_domains = [normalise_domain(d) for d in (client_domains or []) if d]

    is_client = any(host == d or host.endswith(f".{d}") for d in client_domains if d)
    is_competitor = any(host == d or host.endswith(f".{d}") for d in competitor_domains if d)

    if is_client:
        cls = "independent"  # owned property — not competitor
        return cls, False, True, AUTHORITY_PRIOR["independent"]
    if is_competitor:
        return "competitor_owned", True, False, AUTHORITY_PRIOR["competitor_owned"]
    if _GOV.search(host):
        return "government", False, False, AUTHORITY_PRIOR["government"]
    if _ACADEMIC.search(host) or _ACADEMIC.search(full):
        return "academic", False, False, AUTHORITY_PRIOR["academic"]
    if _REVIEW.search(host):
        return "review", False, False, AUTHORITY_PRIOR["review"]
    if _FORUM.search(host):
        return "forum", False, False, AUTHORITY_PRIOR["forum"]
    if _NEWS.search(host):
        return "news", False, False, AUTHORITY_PRIOR["news"]
    if _INDUSTRY.search(host):
        return "industry_publication", False, False, AUTHORITY_PRIOR["industry_publication"]
    return "independent", False, False, AUTHORITY_PRIOR["independent"]


def extract_urls(text: str) -> list[str]:
    """Pull http(s) URLs from an answer excerpt."""
    if not text:
        return []
    found = re.findall(r"https?://[^\s)>\]]+", text, flags=re.IGNORECASE)
    cleaned: list[str] = []
    seen: set[str] = set()
    for url in found:
        url = url.rstrip(".,;\"'")
        key = url.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(url)
    return cleaned


def host_from_url(url: str) -> str:
    return normalise_domain(url)
