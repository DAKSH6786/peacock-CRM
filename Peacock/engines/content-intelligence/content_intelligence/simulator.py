"""Multi-LLM Content Simulator — pre-publish readiness estimate, not a guaranteed ranking.

The deterministic part reuses the same real GEO Score factors (Entity
Authority, Citation Readiness, Answerability, Evidence, Topical Coverage,
Technical AI Accessibility, Brand Authority) applied directly to the draft
text — the exact same measurable signals AI platforms are more likely to
reward, without needing a live model call. When AI plugins are configured,
an optional live critique step broadcasts the draft to each and reports
whether it mentions the brand/topic clearly — never a guaranteed-ranking claim.
"""

from __future__ import annotations

import re
from uuid import uuid4

from crawler.store import StoredPage
from geo_intelligence.gateway import DEFAULT_ENGINE_CODES, ENGINE_META, PeacockAIGateway
from llm_gateway.registry import LLMGateway
from site_intelligence.geo_score import compute_page_geo_score
from site_intelligence.models import GeoScoreBreakdown

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


def _draft_to_page(draft_text: str, *, url: str = "draft://peacock-content-studio") -> StoredPage:
    h1: list[str] = []
    h2: list[str] = []
    h3: list[str] = []
    for match in _HEADING_RE.finditer(draft_text or ""):
        level = len(match.group(1))
        text = match.group(2).strip()
        if level == 1:
            h1.append(text)
        elif level == 2:
            h2.append(text)
        elif level >= 3:
            h3.append(text)

    plain_text = re.sub(r"^#{1,6}\s+", "", draft_text or "", flags=re.MULTILINE)
    word_count = len(plain_text.split())

    return StoredPage(
        id=str(uuid4()),
        url=url,
        canonical=url,
        status_code=200,
        title=h1[0] if h1 else None,
        meta_description=None,
        h1=h1,
        h2=h2,
        h3=h3,
        body_text=plain_text,
        word_count=word_count,
        internal_links=[],
        external_links=re.findall(r"https?://[^\s)\]]+", draft_text or ""),
        images=[],
        schema=[{"@type": "FAQPage"}] if "faq" in (draft_text or "").lower() else [],
        robots=None,
        indexability="indexable",
        crawl_depth=0,
        content_hash=None,
        content_type="text/plain",
        language="en",
        is_js_heavy=False,
        redirect_chain=[],
        fetch_mode="draft",
        status="fetched",
        viewport_meta="width=device-width, initial-scale=1.0",
    )


def simulate_geo_readiness(draft_text: str, *, site_key_terms: list[str] | None = None) -> GeoScoreBreakdown:
    """Deterministic GEO readiness estimate for unpublished draft text."""
    page = _draft_to_page(draft_text)
    return compute_page_geo_score(page, site_key_terms=site_key_terms or [])


async def simulate_multi_llm_readiness(
    *,
    llm_gateway: LLMGateway | None,
    draft_text: str,
    topic: str,
    brand: str,
    site_key_terms: list[str] | None = None,
    engine_codes: list[str] | None = None,
) -> dict:
    """Per-platform readiness estimates — deterministic GEO score (always available)
    plus an optional live-plugin critique when a plugin has a configured API key."""
    breakdown = simulate_geo_readiness(draft_text, site_key_terms=site_key_terms)
    codes = [c for c in (engine_codes or list(DEFAULT_ENGINE_CODES)) if c in ENGINE_META]

    gateway = PeacockAIGateway(llm_gateway)
    live_codes = gateway.available_engine_codes()

    critique_prompt = (
        f"Here is a draft about '{topic}' for the brand '{brand}'. In two sentences, would you be able to "
        f"extract a clear, quotable answer from it, and does it read as trustworthy and specific?\n\n"
        f"---\n{draft_text[:4000]}\n---"
    )
    responses = await gateway.broadcast(
        organisation_id="content-studio",
        research_prompt=critique_prompt,
        engine_codes=codes,
        simulated_responses={},
    )

    per_platform = []
    for response in responses:
        per_platform.append(
            {
                "engine_code": response.engine_code,
                "engine_name": response.engine_name,
                "geo_readiness_score": breakdown.geo_score,
                "live_critique_available": not response.simulated,
                "live_critique": response.content if not response.simulated else None,
                "note": (
                    "Live critique from a configured plugin."
                    if not response.simulated
                    else f"{response.engine_name} plugin has no live API key configured — showing the "
                    "deterministic GEO readiness estimate only."
                ),
            }
        )

    return {
        "topic": topic,
        "brand": brand,
        "geo_score_breakdown": breakdown.to_dict(),
        "per_platform": per_platform,
        "disclaimer": (
            "These are content readiness estimates based on measurable GEO factors and, where available, "
            "a live plugin critique — not a guaranteed ranking or citation outcome on any platform."
        ),
    }
