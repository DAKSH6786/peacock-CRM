"""Strategy generation from Entity Gaps."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from db_models.entity_intelligence import STRATEGY_ACTIONS
from entity_intelligence.scoring import EntityGapResult


@dataclass(frozen=True)
class EntityStrategy:
    target_concept: str
    action_type: str
    priority: str
    title: str
    rationale: str
    recommended_moves: list[str]
    expected_association_lift: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def moves_text(self) -> str:
        return "\n".join(f"- {m}" for m in self.recommended_moves)


def _action_for_gap(gap: EntityGapResult) -> str:
    concept = gap.target_concept.lower()
    if any(k in concept for k in ("executive", "founder", "ceo", "leadership")):
        return "executive_thought_leadership"
    if any(k in concept for k in ("feature", "capability", "module")):
        return "close_feature_narrative_gap"
    if any(k in concept for k in ("location", "region", "country", "city")):
        return "localise_entity_presence"
    if gap.client_association < 0.35 and gap.gap_size >= 0.25:
        return "strengthen_entity_ownership"
    if gap.leading_competitor_association >= 0.75:
        return "competitor_differentiation"
    if "wealth" in concept or "premier" in concept or "product" in concept:
        return "clarify_product_positioning"
    if gap.client_association < 0.5:
        return "publish_pillar_content"
    return "earn_third_party_association"


def _moves(action: str, concept: str, client: str) -> list[str]:
    catalog: dict[str, list[str]] = {
        "strengthen_entity_ownership": [
            f"Publish definitive {client} ownership content for “{concept}”.",
            f"Align product naming, schema, and FAQs so {client}↔{concept} is unambiguous.",
            "Create entity-consistent internal links from hub pages to supporting proof.",
        ],
        "publish_pillar_content": [
            f"Build a pillar page that makes {client} the primary entity for “{concept}”.",
            "Add supporting cluster pages covering adjacent problems, features, and customers.",
            "Ensure extractable definitions and evidence blocks generative systems can cite.",
        ],
        "earn_third_party_association": [
            f"Earn independent publications associating {client} with “{concept}”.",
            "Provide primary-source data journalists and analysts can attribute.",
            "Pursue expert quotes and industry listings that reinforce the entity pair.",
        ],
        "clarify_product_positioning": [
            f"Clarify how {client} products/services map to “{concept}” vs adjacent offers.",
            "Reduce naming collisions that dilute Entity Association Strength.",
            "Publish comparison matrices grounded in verifiable features.",
        ],
        "executive_thought_leadership": [
            f"Activate founder/executive narratives that bind leadership entities to “{concept}”.",
            "Publish attributable expert commentary with clear brand ownership.",
            "Connect people entities to product and industry entities consistently.",
        ],
        "close_feature_narrative_gap": [
            f"Document features that substantiate {client} ownership of “{concept}”.",
            "Ship demos, screenshots, and structured specs competitors already showcase.",
            "Map feature entities to customer problems and industry topics.",
        ],
        "localise_entity_presence": [
            f"Localise pages and sources that connect {client} to “{concept}” by market.",
            "Add location entities with accurate NAP and regional proof points.",
            "Earn local publications that reinforce geo-entity associations.",
        ],
        "competitor_differentiation": [
            f"Contrast {client} vs leading competitors on “{concept}” with evidence, not claims.",
            "Own a differentiated sub-entity (segment, feature, or customer type).",
            "Close proof gaps where competitor association strength is highest.",
        ],
    }
    moves = catalog.get(action, catalog["publish_pillar_content"])
    assert action in STRATEGY_ACTIONS
    return moves


def generate_strategies(
    *,
    gaps: list[EntityGapResult],
    client_brand: str,
    max_strategies: int = 12,
) -> list[EntityStrategy]:
    """Generate actionable strategy from Entity Gaps."""
    strategies: list[EntityStrategy] = []
    for gap in gaps:
        if gap.gap_size < 0.08 and gap.client_association >= 0.7:
            continue  # already strong; skip
        action = _action_for_gap(gap)
        lift = round(min(0.35, 0.1 + gap.gap_size * 0.4), 3)
        priority = gap.severity if gap.severity != "low" else "medium"
        if gap.severity == "low" and gap.gap_size < 0.1:
            priority = "low"
        rationale = (
            f"{gap.summary} Closing this Entity Gap should raise "
            f"{client_brand}↔{gap.target_concept} association strength "
            f"(estimated lift up to +{lift:.2f} under multi-signal scoring)."
        )
        strategies.append(
            EntityStrategy(
                target_concept=gap.target_concept,
                action_type=action,
                priority=priority,
                title=f"Strengthen {client_brand} ↔ {gap.target_concept}",
                rationale=rationale,
                recommended_moves=_moves(action, gap.target_concept, client_brand),
                expected_association_lift=lift,
            )
        )
        if len(strategies) >= max_strategies:
            break

    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    strategies.sort(key=lambda s: (priority_rank.get(s.priority, 9), -s.expected_association_lift))
    return strategies
