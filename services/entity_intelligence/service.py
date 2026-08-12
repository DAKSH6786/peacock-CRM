"""Peacock Entity Intelligence orchestration service."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.entity_intelligence import (
    ASSOCIATION_COMPONENTS,
    ENTITY_TYPES,
    EntityIntelligenceAnalysis,
    EiAssociation,
    EiEntity,
    EiEntityGap,
    EiStrategy,
)
from entity_intelligence.models import (
    AssociationInputSpec,
    EntityIntelligenceReport,
    EntityIntelligenceSpec,
    EntityNodeSpec,
)
from entity_intelligence.scoring import (
    DEFAULT_ASSOCIATION_WEIGHTS,
    AssociationScore,
    AssociationSignal,
    EntityGapResult,
    compute_entity_gaps,
    score_associations,
)
from entity_intelligence.strategy import EntityStrategy, generate_strategies


class EntityIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: EntityIntelligenceSpec,
        created_by: str | None = None,
    ) -> EntityIntelligenceReport:
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")
        if not spec.associations and not spec.entities:
            raise ValueError("At least one entity or association is required")

        weights = spec.association_weights or DEFAULT_ASSOCIATION_WEIGHTS
        analysis = EntityIntelligenceAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.client_brand.strip(),
            industry=spec.industry,
            analysis_status="running",
            methodology="entity_association_multi_signal",
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        entities = self._ensure_entities(spec)
        for ent in entities:
            if ent.entity_type not in ENTITY_TYPES:
                raise ValueError(f"Unsupported entity_type: {ent.entity_type}")
            self.db.add(
                EiEntity(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    canonical_name=ent.canonical_name,
                    entity_type=ent.entity_type,
                    is_client=ent.is_client,
                    is_competitor=ent.is_competitor,
                    aliases=",".join(ent.aliases) if ent.aliases else None,
                    description=ent.description,
                    ownership_brand=ent.ownership_brand,
                )
            )

        signals = [
            AssociationSignal(
                source_entity_name=a.source_entity_name,
                source_entity_type=a.source_entity_type,
                target_entity_name=a.target_entity_name,
                target_entity_type=a.target_entity_type,
                is_client_owned=a.is_client_owned
                or a.source_entity_name.lower() == spec.client_brand.lower(),
                is_competitor_owned=a.is_competitor_owned,
                co_occurrence=a.co_occurrence,
                semantic_proximity=a.semantic_proximity,
                ownership_signal=a.ownership_signal,
                citation_linkage=a.citation_linkage,
                topical_centrality=a.topical_centrality,
                recency=a.recency,
                cross_source_consistency=a.cross_source_consistency,
                observation_count=a.observation_count,
            )
            for a in spec.associations
        ]
        scores = score_associations(signals, weights=weights)

        for score in scores:
            self.db.add(
                EiAssociation(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    source_entity_name=score.source_entity_name,
                    source_entity_type=score.source_entity_type,
                    target_entity_name=score.target_entity_name,
                    target_entity_type=score.target_entity_type,
                    is_client_owned=score.is_client_owned,
                    is_competitor_owned=score.is_competitor_owned,
                    association_strength=score.association_strength,
                    co_occurrence=score.components["co_occurrence"],
                    semantic_proximity=score.components["semantic_proximity"],
                    ownership_signal=score.components["ownership_signal"],
                    citation_linkage=score.components["citation_linkage"],
                    topical_centrality=score.components["topical_centrality"],
                    recency=score.components["recency"],
                    cross_source_consistency=score.components["cross_source_consistency"],
                    observation_count=score.observation_count,
                    component_explanations=score.explanations_json(),
                )
            )

        gaps = compute_entity_gaps(
            client_brand=spec.client_brand,
            associations=scores,
            target_concepts=spec.target_concepts or None,
        )
        gap_id_by_concept: dict[str, str] = {}
        for gap in gaps:
            gap_id = new_uuid()
            gap_id_by_concept[gap.target_concept] = gap_id
            self.db.add(
                EiEntityGap(
                    id=gap_id,
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    target_concept=gap.target_concept,
                    target_entity_type=gap.target_entity_type,
                    client_brand=gap.client_brand,
                    client_association=gap.client_association,
                    leading_competitor_name=gap.leading_competitor_name,
                    leading_competitor_association=gap.leading_competitor_association,
                    competitor_associations_json=json.dumps(gap.competitor_associations),
                    gap_size=gap.gap_size,
                    severity=gap.severity,
                    summary=gap.summary,
                )
            )

        strategies = generate_strategies(gaps=gaps, client_brand=spec.client_brand)
        for strat in strategies:
            self.db.add(
                EiStrategy(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    gap_id=gap_id_by_concept.get(strat.target_concept),
                    target_concept=strat.target_concept,
                    action_type=strat.action_type,
                    priority=strat.priority,
                    title=strat.title,
                    rationale=strat.rationale,
                    recommended_moves=strat.moves_text(),
                    expected_association_lift=strat.expected_association_lift,
                )
            )

        client_ownership = [
            s
            for s in scores
            if s.source_entity_name.lower() == spec.client_brand.lower()
        ]
        client_ownership.sort(key=lambda s: s.association_strength, reverse=True)

        analysis.entity_count = len(entities)
        analysis.association_count = len(scores)
        analysis.gap_count = len(gaps)
        analysis.strategy_count = len(strategies)
        analysis.analysis_status = "ready"
        self.db.commit()

        example_gap = None
        if gaps:
            g = gaps[0]
            example_gap = {
                "target_concept": g.target_concept,
                "associations": {
                    **g.competitor_associations,
                    g.client_brand: g.client_association,
                },
                "gap_size": g.gap_size,
                "severity": g.severity,
                "summary": g.summary,
            }

        return EntityIntelligenceReport(
            analysis_id=analysis.id,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            entity_count=analysis.entity_count,
            association_count=analysis.association_count,
            associations=scores,
            client_ownership=client_ownership,
            gaps=gaps,
            strategies=strategies,
            association_weights=dict(weights),
            example_ownership=[
                {
                    "pair": f"{a.source_entity_name} ↔ {a.target_entity_name}",
                    "association_strength": round(a.association_strength, 2),
                }
                for a in client_ownership[:10]
            ],
            example_gap=example_gap,
        )

    def get_report(
        self, *, analysis_id: str, organisation_id: str
    ) -> EntityIntelligenceReport | None:
        analysis = self.db.scalar(
            select(EntityIntelligenceAnalysis).where(
                EntityIntelligenceAnalysis.id == analysis_id,
                EntityIntelligenceAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        assoc_rows = list(
            self.db.scalars(
                select(EiAssociation)
                .where(EiAssociation.analysis_id == analysis_id)
                .order_by(EiAssociation.association_strength.desc())
            ).all()
        )
        scores = [
            AssociationScore(
                source_entity_name=r.source_entity_name,
                source_entity_type=r.source_entity_type,
                target_entity_name=r.target_entity_name,
                target_entity_type=r.target_entity_type,
                is_client_owned=r.is_client_owned,
                is_competitor_owned=r.is_competitor_owned,
                association_strength=r.association_strength,
                components={
                    "co_occurrence": r.co_occurrence,
                    "semantic_proximity": r.semantic_proximity,
                    "ownership_signal": r.ownership_signal,
                    "citation_linkage": r.citation_linkage,
                    "topical_centrality": r.topical_centrality,
                    "recency": r.recency,
                    "cross_source_consistency": r.cross_source_consistency,
                },
                explanations=json.loads(r.component_explanations or "{}"),
                observation_count=r.observation_count,
            )
            for r in assoc_rows
        ]
        gap_rows = list(
            self.db.scalars(
                select(EiEntityGap)
                .where(EiEntityGap.analysis_id == analysis_id)
                .order_by(EiEntityGap.gap_size.desc())
            ).all()
        )
        gaps = [
            EntityGapResult(
                target_concept=g.target_concept,
                target_entity_type=g.target_entity_type,
                client_brand=g.client_brand,
                client_association=g.client_association,
                competitor_associations=json.loads(g.competitor_associations_json or "{}"),
                leading_competitor_name=g.leading_competitor_name,
                leading_competitor_association=g.leading_competitor_association,
                gap_size=g.gap_size,
                severity=g.severity,
                summary=g.summary,
            )
            for g in gap_rows
        ]
        strat_rows = list(
            self.db.scalars(
                select(EiStrategy).where(EiStrategy.analysis_id == analysis_id)
            ).all()
        )
        strategies = [
            EntityStrategy(
                target_concept=s.target_concept,
                action_type=s.action_type,
                priority=s.priority,
                title=s.title,
                rationale=s.rationale,
                recommended_moves=[
                    line[2:].strip() if line.startswith("- ") else line.strip()
                    for line in (s.recommended_moves or "").splitlines()
                    if line.strip()
                ],
                expected_association_lift=s.expected_association_lift or 0.0,
            )
            for s in strat_rows
        ]
        client_ownership = [
            s
            for s in scores
            if s.source_entity_name.lower() == analysis.client_brand.lower()
        ]
        example_gap = None
        if gaps:
            g = gaps[0]
            example_gap = {
                "target_concept": g.target_concept,
                "associations": {
                    **g.competitor_associations,
                    g.client_brand: g.client_association,
                },
                "gap_size": g.gap_size,
                "severity": g.severity,
                "summary": g.summary,
            }
        return EntityIntelligenceReport(
            analysis_id=analysis.id,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            entity_count=analysis.entity_count,
            association_count=analysis.association_count,
            associations=scores,
            client_ownership=client_ownership,
            gaps=gaps,
            strategies=strategies,
            association_weights=dict(DEFAULT_ASSOCIATION_WEIGHTS),
            example_ownership=[
                {
                    "pair": f"{a.source_entity_name} ↔ {a.target_entity_name}",
                    "association_strength": round(a.association_strength, 2),
                }
                for a in client_ownership[:10]
            ],
            example_gap=example_gap,
        )

    @staticmethod
    def supported_entity_types() -> tuple[str, ...]:
        return ENTITY_TYPES

    @staticmethod
    def association_components() -> tuple[str, ...]:
        return ASSOCIATION_COMPONENTS

    def _ensure_entities(self, spec: EntityIntelligenceSpec) -> list[EntityNodeSpec]:
        by_key: dict[tuple[str, str], EntityNodeSpec] = {}
        for ent in spec.entities:
            key = (ent.canonical_name.lower(), ent.entity_type)
            by_key[key] = ent
        # Derive nodes from associations
        for a in spec.associations:
            sk = (a.source_entity_name.lower(), a.source_entity_type)
            tk = (a.target_entity_name.lower(), a.target_entity_type)
            if sk not in by_key:
                by_key[sk] = EntityNodeSpec(
                    canonical_name=a.source_entity_name,
                    entity_type=a.source_entity_type,
                    is_client=a.source_entity_name.lower() == spec.client_brand.lower(),
                    is_competitor=a.is_competitor_owned,
                )
            if tk not in by_key:
                by_key[tk] = EntityNodeSpec(
                    canonical_name=a.target_entity_name,
                    entity_type=a.target_entity_type,
                )
        # Ensure client brand node
        client_key = (spec.client_brand.lower(), "brand")
        if client_key not in by_key:
            by_key[client_key] = EntityNodeSpec(
                canonical_name=spec.client_brand,
                entity_type="brand",
                is_client=True,
            )
        return list(by_key.values())
