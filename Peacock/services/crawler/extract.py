"""Page extraction utilities for Peacock Crawler."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup

from crawler.url_utils import absolutise, is_same_host, normalise_url


@dataclass(slots=True)
class ImageExtraction:
    src: str
    alt: str | None


@dataclass(slots=True)
class PageExtraction:
    url: str
    final_url: str
    status_code: int
    title: str | None
    meta_description: str | None
    canonical: str | None
    h1: list[str]
    h2: list[str]
    h3: list[str]
    body_text: str
    word_count: int
    internal_links: list[str]
    external_links: list[str]
    images: list[ImageExtraction]
    schema_blocks: list[dict[str, Any]]
    robots: str | None
    indexability: str
    content_type: str
    language: str | None
    content_hash: str
    is_js_heavy: bool
    redirect_chain: list[str] = field(default_factory=list)
    crawl_depth: int = 0
    headers: dict[str, str] = field(default_factory=dict)
    viewport_meta: str | None = None


_SCRIPT_SRC_HINTS = ("react", "vue", "angular", "next", "nuxt", "webpack", "vite")


def _meta_content(soup: BeautifulSoup, *, name: str | None = None, prop: str | None = None) -> str | None:
    if name:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    if prop:
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            return str(tag["content"]).strip()
    return None


def _heading_texts(soup: BeautifulSoup, tag: str) -> list[str]:
    values: list[str] = []
    for node in soup.find_all(tag):
        text = node.get_text(" ", strip=True)
        if text:
            values.append(text[:500])
    return values


def _detect_language(soup: BeautifulSoup, body_text: str) -> str | None:
    html = soup.find("html")
    if html and html.get("lang"):
        return str(html["lang"]).strip()[:32]
    # Extremely light heuristic fallback
    if re.search(r"\b(the|and|with|for)\b", body_text.lower()):
        return "en"
    return None


def _content_type(headers: dict[str, str], soup: BeautifulSoup) -> str:
    header = headers.get("content-type") or headers.get("Content-Type") or ""
    if "json" in header.lower():
        return "application/json"
    if "xml" in header.lower():
        return "application/xml"
    if soup.find("html") is not None:
        return "text/html"
    return header.split(";")[0].strip() or "unknown"


def _robots_directive(soup: BeautifulSoup, headers: dict[str, str]) -> str | None:
    meta = _meta_content(soup, name="robots")
    header = headers.get("x-robots-tag") or headers.get("X-Robots-Tag")
    parts = [p for p in (meta, header) if p]
    return ", ".join(parts) if parts else None


def _indexability(robots: str | None, status_code: int, canonical: str | None, url: str) -> str:
    if status_code >= 400:
        return "non_indexable_status"
    if robots:
        lowered = robots.lower()
        if "noindex" in lowered:
            return "noindex"
    if canonical:
        try:
            if normalise_url(canonical).normalised != normalise_url(url).normalised:
                return "canonicalised"
        except Exception:  # noqa: BLE001
            pass
    return "indexable"


def detect_js_heavy(html: str, body_text: str, *, script_threshold: int, body_char_threshold: int) -> bool:
    soup = BeautifulSoup(html or "", "html.parser")
    scripts = soup.find_all("script")
    external = sum(1 for s in scripts if s.get("src"))
    if external >= script_threshold:
        return True
    joined_src = " ".join(str(s.get("src") or "").lower() for s in scripts)
    if any(hint in joined_src for hint in _SCRIPT_SRC_HINTS):
        return True
    root_markers = soup.select("#__next, #root, #app, [data-reactroot]")
    if root_markers and len(body_text.strip()) < body_char_threshold:
        return True
    return False


def content_hash(text: str) -> str:
    normalised = re.sub(r"\s+", " ", (text or "").strip().lower())
    return hashlib.sha256(normalised.encode("utf-8", errors="ignore")).hexdigest()


def near_duplicate(a: str, b: str, *, threshold: float) -> bool:
    """Cheap token Jaccard similarity for near-duplicate detection."""
    ta = set(re.findall(r"[a-z0-9]{3,}", (a or "").lower()))
    tb = set(re.findall(r"[a-z0-9]{3,}", (b or "").lower()))
    if not ta or not tb:
        return False
    score = len(ta & tb) / len(ta | tb)
    return score >= threshold


def extract_page(
    *,
    request_url: str,
    final_url: str,
    status_code: int,
    html: str,
    headers: dict[str, str],
    seed_host_url: str,
    crawl_depth: int = 0,
    redirect_chain: list[str] | None = None,
    js_heavy_script_threshold: int = 8,
    js_heavy_body_char_threshold: int = 120,
    max_body_chars: int = 200_000,
) -> PageExtraction:
    soup = BeautifulSoup(html or "", "html.parser")

    # Remove non-content noise for body text
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else None
    meta_description = _meta_content(soup, name="description") or _meta_content(soup, prop="og:description")
    canonical = None
    link_canon = soup.find("link", rel=lambda v: v and "canonical" in str(v).lower())
    if link_canon and link_canon.get("href"):
        canonical = absolutise(str(link_canon["href"]), final_url)

    h1 = _heading_texts(soup, "h1")
    h2 = _heading_texts(soup, "h2")
    h3 = _heading_texts(soup, "h3")
    body_text = soup.get_text(" ", strip=True)[:max_body_chars]
    words = [w for w in re.split(r"\s+", body_text) if w]
    word_count = len(words)

    internal: list[str] = []
    external: list[str] = []
    # Re-parse for links/images/schema from original HTML
    raw = BeautifulSoup(html or "", "html.parser")
    for anchor in raw.find_all("a", href=True):
        abs_url = absolutise(str(anchor["href"]), final_url)
        if not abs_url:
            continue
        if is_same_host(abs_url, seed_host_url):
            internal.append(abs_url)
        else:
            external.append(abs_url)
    internal = list(dict.fromkeys(internal))
    external = list(dict.fromkeys(external))

    images: list[ImageExtraction] = []
    for img in raw.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        abs_src = absolutise(str(src), final_url) or str(src)
        alt = img.get("alt")
        images.append(ImageExtraction(src=abs_src, alt=str(alt).strip() if alt is not None else None))

    schema_blocks: list[dict[str, Any]] = []
    for script in raw.find_all("script", attrs={"type": "application/ld+json"}):
        text = script.string or script.get_text() or ""
        text = text.strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
            if isinstance(payload, list):
                schema_blocks.extend([p for p in payload if isinstance(p, dict)])
            elif isinstance(payload, dict):
                schema_blocks.append(payload)
        except json.JSONDecodeError:
            schema_blocks.append({"raw": text[:5000], "parse_error": True})

    viewport_meta = _meta_content(raw, name="viewport")
    robots = _robots_directive(raw, headers)
    indexability = _indexability(robots, status_code, canonical, final_url)
    language = _detect_language(raw, body_text)
    ctype = _content_type(headers, raw)
    js_heavy = detect_js_heavy(
        html,
        body_text,
        script_threshold=js_heavy_script_threshold,
        body_char_threshold=js_heavy_body_char_threshold,
    )

    return PageExtraction(
        url=request_url,
        final_url=final_url,
        status_code=status_code,
        title=title,
        meta_description=meta_description,
        canonical=canonical,
        h1=h1,
        h2=h2,
        h3=h3,
        body_text=body_text,
        word_count=word_count,
        internal_links=internal,
        external_links=external,
        images=images,
        schema_blocks=schema_blocks,
        robots=robots,
        indexability=indexability,
        content_type=ctype,
        language=language,
        content_hash=content_hash(body_text),
        is_js_heavy=js_heavy,
        redirect_chain=list(redirect_chain or []),
        crawl_depth=crawl_depth,
        headers={k.lower(): v for k, v in headers.items()},
        viewport_meta=viewport_meta,
    )
