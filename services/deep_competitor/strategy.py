"""Differentiated strategy — leapfrog rivals without copying content."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from db_models.deep_competitor import FORBIDDEN_RECOMMENDATION_MODES
from deep_competitor.delta import CompetitiveDelta
from deep_competitor.discovery import DiscoveredCompetitor
from deep_competitor.reverse_content import ContentDiffResult


@dataclass(frozen=True)
class DifferentiatedStrategy:
    competitor_domain: str | None
    priority: str
    title: str
    rationale: str
    differentiated_moves: list[str]
    leapfrog_angle: str
    copy_competitor_content_rejected: bool = True
    forbidden_modes_note: str = (
        "Never copy, paraphrase, scrape, or thinly rewrite competitor content. "
        f"Forbidden modes: {', '.join(FORBIDDEN_RECOMMENDATION_MODES)}."
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def moves_text(self) -> str:
        return "\n".join(f"- {m}" for m in self.differentiated_moves)


def generate_differentiated_strategies(
    *,
    competitors: list[DiscoveredCompetitor],
    deltas: list[CompetitiveDelta],
    content_diffs: list[ContentDiffResult],
    client_brand: str,
    max_strategies: int = 10,
) -> list[DifferentiatedStrategy]:
    strategies: list[DifferentiatedStrategy] = []

    # Per top rival: aggregate strongest deltas
    by_domain: dict[str, list[CompetitiveDelta]] = {}
    for d in deltas:
        by_domain.setdefault(d.competitor_domain, []).append(d)

    rival_meta = {c.domain: c for c in competitors}

    for domain, domain_deltas in sorted(
        by_domain.items(),
        key=lambda kv: max(x.delta for x in kv[1]),
        reverse=True,
    ):
        top = domain_deltas[0]
        meta = rival_meta.get(domain)
        cats = ", ".join(meta.categories) if meta else "competitor"
        priority = (
            "critical"
            if top.gap_difficulty == "hard"
            else ("high" if top.gap_difficulty == "moderate" else "medium")
        )
        moves = [
            top.how_to_close,
            top.how_to_leapfrog,
            f"Document proof points unique to {client_brand} that {domain} cannot claim.",
            "Do not copy or paraphrase their pages — invent a superior, attributable narrative.",
        ]
        # Attach one content-diff insight if present
        related_diffs = [c for c in content_diffs if c.competitor_domain == domain][:2]
        for diff in related_diffs:
            moves.append(
                f"On {diff.dimension.replace('_', ' ')}: {diff.differentiated_recommendation}"
            )

        strategies.append(
            DifferentiatedStrategy(
                competitor_domain=domain,
                priority=priority,
                title=f"Leapfrog {meta.name if meta else domain} on {top.dimension.replace('_', ' ')}",
                rationale=(
                    f"{top.where_stronger} Why: {top.why_stronger} "
                    f"Categories: {cats}. Gap difficulty: {top.gap_difficulty}."
                ),
                differentiated_moves=moves,
                leapfrog_angle=top.how_to_leapfrog,
            )
        )
        if len(strategies) >= max_strategies:
            break

    if not strategies and competitors:
        top_rival = competitors[0]
        strategies.append(
            DifferentiatedStrategy(
                competitor_domain=top_rival.domain,
                priority="medium",
                title=f"Differentiate against {top_rival.name}",
                rationale=top_rival.discovery_rationale,
                differentiated_moves=[
                    "Identify intents they win that you can reframe with proprietary proof.",
                    "Build entity ownership on concepts they under-define.",
                    "Never copy their content; ship original assets.",
                ],
                leapfrog_angle="Own a contested concept with primary research.",
            )
        )

    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    strategies.sort(key=lambda s: priority_rank.get(s.priority, 9))
    return strategies
