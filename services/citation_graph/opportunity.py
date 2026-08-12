"""Source Opportunity Engine — ethical recommendations only.

Detects influential citation domains where the client is under-represented
and recommends legitimate actions (PR, research, partnerships, corrections).
Never suggests manipulative spam.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from db_models.citation_graph import FORBIDDEN_TACTICS, OPPORTUNITY_TYPES
from citation_graph.scoring import DomainInfluenceBreakdown

# Minimum domain answer influence to consider an opportunity
MIN_DOMAIN_INFLUENCE_PCT = 8.0
# Client must be clearly under-indexed vs domain influence
MAX_CLIENT_MENTION_PCT_FOR_OPP = 15.0


@dataclass(frozen=True)
class SourceOpportunity:
    cited_domain: str
    source_class: str
    opportunity_type: str
    priority: str
    domain_answer_influence_pct: float
    client_mention_pct: float
    top_competitor_name: str | None
    top_competitor_mention_pct: float
    title: str
    rationale: str
    recommended_actions: list[str]
    manipulative_spam_rejected: bool = True
    forbidden_tactics_note: str = (
        "Never use spam, link farms, fake reviews, cloaking, astroturfing, "
        "or undisclosed paid placements."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def actions_text(self) -> str:
        return "\n".join(f"- {a}" for a in self.recommended_actions)


def _priority(influence_pct: float, client_pct: float, competitor_pct: float) -> str:
    gap = influence_pct - client_pct
    if influence_pct >= 20 and client_pct <= 5 and competitor_pct >= 40:
        return "critical"
    if gap >= 20 or (influence_pct >= 15 and client_pct < 8):
        return "high"
    if gap >= 10:
        return "medium"
    return "low"


def _opportunity_type(source_class: str, client_pct: float, competitor_pct: float) -> str:
    if source_class == "news":
        return "pr_opportunity"
    if source_class == "academic":
        return "original_research"
    if source_class == "industry_publication":
        return "expert_contribution"
    if source_class == "review":
        return "review_improvement"
    if source_class == "government":
        return "listing_correction"
    if source_class == "forum":
        return "content_relationship"
    if source_class == "competitor_owned":
        return "content_relationship"
    if competitor_pct > client_pct * 2:
        return "source_partnership"
    return "source_partnership"


def _actions(opportunity_type: str, domain: str) -> list[str]:
    catalog: dict[str, list[str]] = {
        "pr_opportunity": [
            f"Pitch original data or customer stories to editors citing {domain}.",
            "Offer an attributable expert quote for future roundups.",
            "Publish a newsworthy study journalists can cite with clear methodology.",
        ],
        "expert_contribution": [
            f"Propose a bylined expert contribution or interview relevant to {domain}.",
            "Share peer-reviewed or practitioner insights editors can verify.",
            "Join industry panels and ensure accurate brand attribution.",
        ],
        "original_research": [
            "Commission or publish original research with open methodology.",
            "Release downloadable datasets or benchmarks others can cite.",
            "Partner with academic or industry researchers for co-authored work.",
        ],
        "source_partnership": [
            f"Build a legitimate content relationship with {domain} (guest data, co-marketing).",
            "Ensure product facts on that source are accurate and up to date.",
            "Offer primary-source documentation editors prefer over secondary summaries.",
        ],
        "listing_correction": [
            f"Audit the {domain} listing for factual errors about your brand.",
            "Submit corrections through official channels with supporting evidence.",
            "Maintain a public fact sheet that sources can cite.",
        ],
        "review_improvement": [
            "Encourage verified customer reviews through legitimate programs only.",
            "Respond helpfully to existing reviews; never fabricate feedback.",
            "Improve product gaps that reviewers repeatedly cite.",
        ],
        "content_relationship": [
            f"Participate helpfully in discussions where {domain} is cited — no spam.",
            "Publish evergreen explainers that community moderators can reference.",
            "Correct misconceptions with transparent, citable primary sources.",
        ],
    }
    actions = catalog.get(opportunity_type, catalog["source_partnership"])
    # Explicit anti-spam guardrail always appended
    actions = [
        *actions,
        "Do not buy fake citations, scrape content, or run manipulative spam campaigns.",
    ]
    assert opportunity_type in OPPORTUNITY_TYPES
    return actions


def detect_source_opportunities(
    *,
    domain_scores: list[DomainInfluenceBreakdown],
    client_brand: str,
) -> list[SourceOpportunity]:
    """Find domains that influence answers while the client is under-mentioned."""
    _ = client_brand
    opportunities: list[SourceOpportunity] = []

    for score in domain_scores:
        if score.is_client_owned:
            continue
        influence_pct = round(100.0 * score.observation_share, 2)
        client_pct = round(100.0 * score.client_mention_rate, 2)
        competitor_pct = round(100.0 * score.top_competitor_mention_rate, 2)

        if influence_pct < MIN_DOMAIN_INFLUENCE_PCT:
            continue
        if client_pct > MAX_CLIENT_MENTION_PCT_FOR_OPP and competitor_pct <= client_pct:
            continue
        # Opportunity: domain is influential and client is weak relative to influence
        if client_pct >= influence_pct * 0.75 and competitor_pct <= client_pct:
            continue

        opp_type = _opportunity_type(
            score.source_class, client_pct, competitor_pct
        )
        priority = _priority(influence_pct, client_pct, competitor_pct)
        competitor_clause = ""
        if score.top_competitor_name:
            competitor_clause = (
                f" {score.top_competitor_name} is mentioned in {competitor_pct:.0f}% "
                f"of answers that cite this domain."
            )

        rationale = (
            f"This source influences {influence_pct:.0f}% of AI answers in this topic "
            f"cluster. Your brand is mentioned in {client_pct:.0f}%."
            f"{competitor_clause} "
            f"Citation Influence Score={score.citation_influence_score:.1f} "
            f"(explainable multi-component). "
            f"Recommend legitimate outreach only — forbidden: "
            f"{', '.join(FORBIDDEN_TACTICS)}."
        )
        opportunities.append(
            SourceOpportunity(
                cited_domain=score.cited_domain,
                source_class=score.source_class,
                opportunity_type=opp_type,
                priority=priority,
                domain_answer_influence_pct=influence_pct,
                client_mention_pct=client_pct,
                top_competitor_name=score.top_competitor_name,
                top_competitor_mention_pct=competitor_pct,
                title=f"Earn ethical presence on {score.cited_domain}",
                rationale=rationale,
                recommended_actions=_actions(opp_type, score.cited_domain),
            )
        )

    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    opportunities.sort(
        key=lambda o: (
            priority_rank.get(o.priority, 9),
            -o.domain_answer_influence_pct,
            o.client_mention_pct,
        )
    )
    return opportunities
