"""Deep Competitor Intelligence orchestration service."""

from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.deep_competitor import (
    FORBIDDEN_RECOMMENDATION_MODES,
    DeepCompetitorAnalysis,
    DcCompetitiveDelta,
    DcCompetitorProfile,
    DcContentDiff,
    DcDifferentiatedStrategy,
)
from deep_competitor.delta import (
    CompetitiveDelta,
    DimensionScoreInput,
    compute_deltas,
)
from deep_competitor.discovery import (
    DiscoveredCompetitor,
    discover_competitors,
)
from deep_competitor.models import DeepCompetitorReport, DeepCompetitorSpec
from deep_competitor.reverse_content import (
    ContentDiffResult,
    reverse_engineer_content,
)
from deep_competitor.strategy import DifferentiatedStrategy, generate_differentiated_strategies


class DeepCompetitorService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: DeepCompetitorSpec,
        created_by: str | None = None,
    ) -> DeepCompetitorReport:
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")
        if not spec.client_domain.strip():
            raise ValueError("client_domain is required")
        if not spec.discovery_candidates:
            raise ValueError(
                "discovery_candidates required — Deep Competitor Intelligence "
                "discovers rivals dynamically and is not limited to four manual domains"
            )

        analysis = DeepCompetitorAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.client_brand.strip(),
            client_domain=spec.client_domain.strip().lower().removeprefix("www."),
            topic_cluster=spec.topic_cluster,
            analysis_status="running",
            methodology="deep_competitor_multi_category",
            copy_competitor_content_rejected=True,
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        competitors = discover_competitors(
            spec.discovery_candidates, min_rivalry=spec.min_rivalry
        )
        # Exclude client domain from discoveries
        competitors = [
            c for c in competitors if c.domain != analysis.client_domain
        ]

        for comp in competitors:
            self.db.add(
                DcCompetitorProfile(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    name=comp.name,
                    domain=comp.domain,
                    categories=comp.categories_csv(),
                    discovery_method=comp.discovery_method,
                    serp_overlap=comp.signals["serp_overlap"],
                    keyword_overlap=comp.signals["keyword_overlap"],
                    topic_overlap=comp.signals["topic_overlap"],
                    ai_mention_overlap=comp.signals["ai_mention_overlap"],
                    citation_overlap=comp.signals["citation_overlap"],
                    entity_similarity=comp.signals["entity_similarity"],
                    product_similarity=comp.signals["product_similarity"],
                    overall_rivalry_score=comp.overall_rivalry_score,
                    is_direct_business_competitor=comp.is_direct_business_competitor,
                    discovery_rationale=comp.discovery_rationale,
                )
            )

        # Auto-fill dimension scores from discovery signals when not provided
        dim_inputs = list(spec.dimension_scores)
        if not dim_inputs:
            dim_inputs = self._default_dimension_scores(competitors)
        deltas = compute_deltas(dim_inputs)
        for delta in deltas:
            self.db.add(
                DcCompetitiveDelta(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    competitor_domain=delta.competitor_domain,
                    competitor_name=delta.competitor_name,
                    dimension=delta.dimension,
                    where_stronger=delta.where_stronger,
                    why_stronger=delta.why_stronger,
                    gap_difficulty=delta.gap_difficulty,
                    gap_difficulty_score=delta.gap_difficulty_score,
                    how_to_close=delta.how_to_close,
                    how_to_leapfrog=delta.how_to_leapfrog,
                    client_score=delta.client_score,
                    competitor_score=delta.competitor_score,
                    delta=delta.delta,
                    evidence=delta.evidence,
                )
            )

        content_diffs = reverse_engineer_content(spec.content_comparisons)
        for diff in content_diffs:
            self.db.add(
                DcContentDiff(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    competitor_domain=diff.competitor_domain,
                    competitor_url=diff.competitor_url,
                    client_url=diff.client_url,
                    dimension=diff.dimension,
                    competitor_advantage=diff.competitor_advantage,
                    client_score=diff.client_score,
                    competitor_score=diff.competitor_score,
                    evidence_summary=diff.evidence_summary,
                    differentiated_recommendation=diff.differentiated_recommendation,
                    copy_rejected=True,
                )
            )

        strategies = generate_differentiated_strategies(
            competitors=competitors,
            deltas=deltas,
            content_diffs=content_diffs,
            client_brand=spec.client_brand,
        )
        forbidden_note = (
            "Never copy, paraphrase, scrape, or thinly rewrite competitor content. "
            f"Forbidden: {', '.join(FORBIDDEN_RECOMMENDATION_MODES)}."
        )
        for strat in strategies:
            self.db.add(
                DcDifferentiatedStrategy(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    competitor_domain=strat.competitor_domain,
                    priority=strat.priority,
                    title=strat.title,
                    rationale=strat.rationale,
                    differentiated_moves=strat.moves_text(),
                    leapfrog_angle=strat.leapfrog_angle,
                    copy_competitor_content_rejected=True,
                    forbidden_modes_note=forbidden_note,
                )
            )

        cat_counts: Counter[str] = Counter()
        for c in competitors:
            for cat in c.categories:
                cat_counts[cat] += 1

        analysis.discovered_count = len(competitors)
        analysis.delta_count = len(deltas)
        analysis.content_diff_count = len(content_diffs)
        analysis.strategy_count = len(strategies)
        analysis.analysis_status = "ready"
        self.db.commit()

        example_delta = deltas[0].to_dict() if deltas else None
        return DeepCompetitorReport(
            analysis_id=analysis.id,
            client_brand=analysis.client_brand,
            client_domain=analysis.client_domain,
            methodology=analysis.methodology,
            copy_competitor_content_rejected=True,
            competitors=competitors,
            deltas=deltas,
            content_diffs=content_diffs,
            strategies=strategies,
            category_breakdown=dict(cat_counts),
            example_discovery=[
                {
                    "domain": c.domain,
                    "categories": c.categories,
                    "rivalry": c.overall_rivalry_score,
                    "business_competitor": c.is_direct_business_competitor,
                }
                for c in competitors[:8]
            ],
            example_delta=example_delta,
        )

    def get_report(
        self, *, analysis_id: str, organisation_id: str
    ) -> DeepCompetitorReport | None:
        analysis = self.db.scalar(
            select(DeepCompetitorAnalysis).where(
                DeepCompetitorAnalysis.id == analysis_id,
                DeepCompetitorAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        profiles = list(
            self.db.scalars(
                select(DcCompetitorProfile)
                .where(DcCompetitorProfile.analysis_id == analysis_id)
                .order_by(DcCompetitorProfile.overall_rivalry_score.desc())
            ).all()
        )
        competitors = [
            DiscoveredCompetitor(
                name=p.name,
                domain=p.domain,
                categories=[c for c in p.categories.split(",") if c],
                discovery_method=p.discovery_method,
                signals={
                    "serp_overlap": p.serp_overlap,
                    "keyword_overlap": p.keyword_overlap,
                    "topic_overlap": p.topic_overlap,
                    "ai_mention_overlap": p.ai_mention_overlap,
                    "citation_overlap": p.citation_overlap,
                    "entity_similarity": p.entity_similarity,
                    "product_similarity": p.product_similarity,
                },
                overall_rivalry_score=p.overall_rivalry_score,
                is_direct_business_competitor=p.is_direct_business_competitor,
                discovery_rationale=p.discovery_rationale,
            )
            for p in profiles
        ]
        delta_rows = list(
            self.db.scalars(
                select(DcCompetitiveDelta)
                .where(DcCompetitiveDelta.analysis_id == analysis_id)
                .order_by(DcCompetitiveDelta.delta.desc())
            ).all()
        )
        deltas = [
            CompetitiveDelta(
                competitor_domain=r.competitor_domain,
                competitor_name=r.competitor_name,
                dimension=r.dimension,
                where_stronger=r.where_stronger,
                why_stronger=r.why_stronger,
                gap_difficulty=r.gap_difficulty,
                gap_difficulty_score=r.gap_difficulty_score,
                how_to_close=r.how_to_close,
                how_to_leapfrog=r.how_to_leapfrog,
                client_score=r.client_score,
                competitor_score=r.competitor_score,
                delta=r.delta,
                evidence=r.evidence,
            )
            for r in delta_rows
        ]
        diff_rows = list(
            self.db.scalars(
                select(DcContentDiff).where(DcContentDiff.analysis_id == analysis_id)
            ).all()
        )
        content_diffs = [
            ContentDiffResult(
                competitor_domain=r.competitor_domain,
                competitor_url=r.competitor_url,
                client_url=r.client_url,
                dimension=r.dimension,
                competitor_advantage=r.competitor_advantage,
                client_score=r.client_score,
                competitor_score=r.competitor_score,
                evidence_summary=r.evidence_summary,
                differentiated_recommendation=r.differentiated_recommendation,
                copy_rejected=r.copy_rejected,
            )
            for r in diff_rows
        ]
        strat_rows = list(
            self.db.scalars(
                select(DcDifferentiatedStrategy).where(
                    DcDifferentiatedStrategy.analysis_id == analysis_id
                )
            ).all()
        )
        strategies = [
            DifferentiatedStrategy(
                competitor_domain=s.competitor_domain,
                priority=s.priority,
                title=s.title,
                rationale=s.rationale,
                differentiated_moves=[
                    line[2:].strip() if line.startswith("- ") else line.strip()
                    for line in (s.differentiated_moves or "").splitlines()
                    if line.strip()
                ],
                leapfrog_angle=s.leapfrog_angle,
                copy_competitor_content_rejected=s.copy_competitor_content_rejected,
                forbidden_modes_note=s.forbidden_modes_note,
            )
            for s in strat_rows
        ]
        cat_counts: Counter[str] = Counter()
        for c in competitors:
            for cat in c.categories:
                cat_counts[cat] += 1
        return DeepCompetitorReport(
            analysis_id=analysis.id,
            client_brand=analysis.client_brand,
            client_domain=analysis.client_domain,
            methodology=analysis.methodology,
            copy_competitor_content_rejected=True,
            competitors=competitors,
            deltas=deltas,
            content_diffs=content_diffs,
            strategies=strategies,
            category_breakdown=dict(cat_counts),
            example_discovery=[
                {
                    "domain": c.domain,
                    "categories": c.categories,
                    "rivalry": c.overall_rivalry_score,
                    "business_competitor": c.is_direct_business_competitor,
                }
                for c in competitors[:8]
            ],
            example_delta=deltas[0].to_dict() if deltas else None,
        )

    @staticmethod
    def _default_dimension_scores(
        competitors: list[DiscoveredCompetitor],
    ) -> list[DimensionScoreInput]:
        """Derive comparative dimension scores from discovery signals."""
        mapping = [
            ("serp_overlap", "serp_presence"),
            ("keyword_overlap", "search_visibility"),
            ("topic_overlap", "content_depth"),
            ("ai_mention_overlap", "ai_visibility"),
            ("citation_overlap", "citation_authority"),
            ("entity_similarity", "entity_ownership"),
            ("product_similarity", "product_coverage"),
        ]
        inputs: list[DimensionScoreInput] = []
        for comp in competitors:
            for signal_key, dimension in mapping:
                rival = comp.signals.get(signal_key, 0.0)
                # Client baseline assumed mid when unknown — delta engine skips tiny gaps
                client = max(0.15, rival - 0.25)
                inputs.append(
                    DimensionScoreInput(
                        competitor_domain=comp.domain,
                        competitor_name=comp.name,
                        dimension=dimension,
                        client_score=client,
                        competitor_score=rival,
                        evidence=f"Derived from discovery signal {signal_key}={rival:.2f}",
                    )
                )
        return inputs
