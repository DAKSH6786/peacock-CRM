"""Peacock Citation Graph orchestration service."""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from citation_graph.classify import classify_source, extract_urls, host_from_url
from citation_graph.models import (
    CitationGraphReport,
    CitationGraphSpec,
    CitationSpec,
    EntityMentionSpec,
    ObservationSpec,
    PathwayView,
)
from citation_graph.opportunity import detect_source_opportunities
from citation_graph.scoring import (
    DEFAULT_CIS_WEIGHTS,
    CitationEvent,
    DomainInfluenceBreakdown,
    aggregate_domain_scores,
    page_path_from_url,
)
from db_models.base import new_uuid
from db_models.citation_graph import (
    FORBIDDEN_TACTICS,
    PATHWAY_NODE_KINDS,
    CitationGraphAnalysis,
    CgCitation,
    CgDomainScore,
    CgEntityMention,
    CgObservation,
    CgPathway,
    CgSourceOpportunity,
)


class CitationGraphService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: CitationGraphSpec,
        created_by: str | None = None,
    ) -> CitationGraphReport:
        if not spec.observations:
            raise ValueError("At least one generative observation is required")
        if not spec.topic_cluster.strip():
            raise ValueError("topic_cluster is required")
        if not spec.client_brand.strip():
            raise ValueError("client_brand is required")

        weights = spec.cis_weights or DEFAULT_CIS_WEIGHTS

        analysis = CitationGraphAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            topic_cluster=spec.topic_cluster.strip(),
            client_brand=spec.client_brand.strip(),
            analysis_status="running",
            methodology="citation_influence_multi_component",
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        events: list[CitationEvent] = []
        pathway_views: list[PathwayView] = []
        citation_total = 0

        for obs_spec in spec.observations:
            topic = (obs_spec.topic_label or spec.topic_cluster).strip()
            obs = CgObservation(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                analysis_id=analysis.id,
                engine_code=obs_spec.engine_code.strip().lower(),
                prompt_text=obs_spec.prompt_text,
                answer_excerpt=obs_spec.answer_excerpt or None,
                observed_at=datetime.now(UTC),
                model_code=obs_spec.model_code,
                topic_label=topic,
            )
            self.db.add(obs)
            self.db.flush()

            entities = self._resolve_entities(obs_spec, spec)
            for ent in entities:
                self.db.add(
                    CgEntityMention(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        observation_id=obs.id,
                        entity_name=ent.entity_name,
                        is_client=ent.is_client,
                        is_competitor=ent.is_competitor,
                        mentioned=ent.mentioned,
                        position_hint=ent.position_hint,
                    )
                )

            client_mentioned = any(e.is_client and e.mentioned for e in entities)
            competitor_names = [
                e.entity_name for e in entities if e.is_competitor and e.mentioned
            ]

            citations = self._resolve_citations(obs_spec, spec)
            prompt_fp = hashlib.sha256(obs_spec.prompt_text.encode()).hexdigest()[:16]

            for cite in citations:
                domain = host_from_url(cite.cited_url)
                if not domain:
                    continue
                source_class, is_comp, is_client, auth_prior = classify_source(
                    url=cite.cited_url,
                    domain=domain,
                    competitor_domains=spec.competitor_domains,
                    client_domains=spec.client_domains,
                )
                if cite.source_class:
                    source_class = cite.source_class
                authority = (
                    cite.authority_proxy
                    if cite.authority_proxy is not None
                    else auth_prior
                )
                page_path = page_path_from_url(cite.cited_url)
                row = CgCitation(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    observation_id=obs.id,
                    cited_url=cite.cited_url,
                    cited_domain=domain,
                    page_path=page_path,
                    source_class=source_class,
                    is_competitor_owned=is_comp,
                    is_client_owned=is_client,
                    prominence=max(0.0, min(1.0, cite.prominence)),
                    freshness_days=cite.freshness_days,
                    authority_proxy=max(0.0, min(1.0, authority)),
                    position_in_answer=cite.position_in_answer,
                )
                self.db.add(row)
                self.db.flush()
                citation_total += 1

                # Pathway: Engine → Prompt → Answer → Citation → Domain → Page → Entity → Topic
                primary_entity = next(
                    (e.entity_name for e in entities if e.mentioned and e.is_client),
                    None,
                )
                if primary_entity is None:
                    primary_entity = next(
                        (e.entity_name for e in entities if e.mentioned and e.is_competitor),
                        None,
                    )
                if primary_entity is None:
                    primary_entity = next(
                        (e.entity_name for e in entities if e.mentioned),
                        None,
                    )

                pathway_key = hashlib.sha256(
                    f"{obs.engine_code}|{prompt_fp}|{domain}|{page_path}|{topic}".encode()
                ).hexdigest()[:24]
                self.db.add(
                    CgPathway(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        analysis_id=analysis.id,
                        observation_id=obs.id,
                        citation_id=row.id,
                        engine_code=obs.engine_code,
                        prompt_fingerprint=prompt_fp,
                        answer_id=obs.id,
                        cited_url=cite.cited_url,
                        cited_domain=domain,
                        page_path=page_path,
                        entity_name=primary_entity,
                        topic_label=topic,
                        source_class=source_class,
                        pathway_key=pathway_key,
                    )
                )
                pathway_views.append(
                    PathwayView(
                        engine_code=obs.engine_code,
                        prompt_fingerprint=prompt_fp,
                        answer_id=obs.id,
                        cited_url=cite.cited_url,
                        cited_domain=domain,
                        page_path=page_path,
                        entity_name=primary_entity,
                        topic_label=topic,
                        source_class=source_class,
                        pathway_key=pathway_key,
                    )
                )

                events.append(
                    CitationEvent(
                        observation_id=obs.id,
                        engine_code=obs.engine_code,
                        prompt_text=obs.prompt_text,
                        topic_label=topic,
                        cited_url=cite.cited_url,
                        cited_domain=domain,
                        page_path=page_path,
                        source_class=source_class,
                        is_competitor_owned=is_comp,
                        is_client_owned=is_client,
                        prominence=row.prominence,
                        freshness_days=cite.freshness_days,
                        authority_proxy=row.authority_proxy,
                        position_in_answer=cite.position_in_answer,
                        client_mentioned=client_mentioned,
                        competitor_names_mentioned=competitor_names,
                    )
                )

        domain_scores = aggregate_domain_scores(
            events=events,
            total_observations=len(spec.observations),
            weights=weights,
        )
        opportunities = detect_source_opportunities(
            domain_scores=domain_scores,
            client_brand=spec.client_brand,
        )

        for score in domain_scores:
            self.db.add(
                CgDomainScore(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    cited_domain=score.cited_domain,
                    source_class=score.source_class,
                    is_citation_hub=score.is_citation_hub,
                    is_competitor_owned=score.is_competitor_owned,
                    is_client_owned=score.is_client_owned,
                    citation_influence_score=score.citation_influence_score,
                    citation_frequency=score.components["citation_frequency"],
                    cross_engine_citation=score.components["cross_engine_citation"],
                    topic_coverage=score.components["topic_coverage"],
                    prominence=score.components["prominence"],
                    freshness=score.components["freshness"],
                    authority_proxy=score.components["authority_proxy"],
                    brand_association=score.components["brand_association"],
                    citation_diversity=score.components["citation_diversity"],
                    citation_count=score.citation_count,
                    engine_count=score.engine_count,
                    page_count=score.page_count,
                    observation_share=score.observation_share,
                    client_mention_rate=score.client_mention_rate,
                    competitor_mention_rate=score.competitor_mention_rate,
                    component_explanations=score.explanations_json(),
                )
            )

        for opp in opportunities:
            self.db.add(
                CgSourceOpportunity(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    cited_domain=opp.cited_domain,
                    source_class=opp.source_class,
                    opportunity_type=opp.opportunity_type,
                    priority=opp.priority,
                    domain_answer_influence_pct=opp.domain_answer_influence_pct,
                    client_mention_pct=opp.client_mention_pct,
                    top_competitor_name=opp.top_competitor_name,
                    top_competitor_mention_pct=opp.top_competitor_mention_pct,
                    title=opp.title,
                    rationale=opp.rationale,
                    recommended_actions=opp.actions_text(),
                    manipulative_spam_rejected=True,
                    forbidden_tactics_note=(
                        "Forbidden tactics: " + ", ".join(FORBIDDEN_TACTICS)
                    ),
                )
            )

        class_counts = Counter(e.source_class for e in events)
        analysis.observation_count = len(spec.observations)
        analysis.citation_count = citation_total
        analysis.domain_count = len(domain_scores)
        analysis.pathway_count = len(pathway_views)
        analysis.opportunity_count = len(opportunities)
        analysis.analysis_status = "ready"
        self.db.commit()

        hubs = [d for d in domain_scores if d.is_citation_hub]
        return CitationGraphReport(
            analysis_id=analysis.id,
            topic_cluster=analysis.topic_cluster,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            observation_count=analysis.observation_count,
            citation_count=analysis.citation_count,
            domain_count=analysis.domain_count,
            pathway_count=analysis.pathway_count,
            domains=domain_scores,
            hubs=hubs,
            pathways_sample=pathway_views[:100],
            opportunities=opportunities,
            source_class_breakdown=dict(class_counts),
            cis_weights=dict(weights),
            manipulative_spam_rejected=True,
        )

    def get_report(
        self, *, analysis_id: str, organisation_id: str
    ) -> CitationGraphReport | None:
        analysis = self.db.scalar(
            select(CitationGraphAnalysis).where(
                CitationGraphAnalysis.id == analysis_id,
                CitationGraphAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        scores = list(
            self.db.scalars(
                select(CgDomainScore)
                .where(CgDomainScore.analysis_id == analysis_id)
                .order_by(CgDomainScore.citation_influence_score.desc())
            ).all()
        )
        domains: list[DomainInfluenceBreakdown] = []
        for s in scores:
            import json

            explanations = {}
            if s.component_explanations:
                explanations = json.loads(s.component_explanations)
            domains.append(
                DomainInfluenceBreakdown(
                    cited_domain=s.cited_domain,
                    source_class=s.source_class,
                    is_citation_hub=s.is_citation_hub,
                    is_competitor_owned=s.is_competitor_owned,
                    is_client_owned=s.is_client_owned,
                    citation_influence_score=s.citation_influence_score,
                    components={
                        "citation_frequency": s.citation_frequency,
                        "cross_engine_citation": s.cross_engine_citation,
                        "topic_coverage": s.topic_coverage,
                        "prominence": s.prominence,
                        "freshness": s.freshness,
                        "authority_proxy": s.authority_proxy,
                        "brand_association": s.brand_association,
                        "citation_diversity": s.citation_diversity,
                    },
                    explanations=explanations,
                    citation_count=s.citation_count,
                    engine_count=s.engine_count,
                    page_count=s.page_count,
                    observation_share=s.observation_share,
                    client_mention_rate=s.client_mention_rate,
                    competitor_mention_rate=s.competitor_mention_rate,
                    top_competitor_name=None,
                    top_competitor_mention_rate=0.0,
                    engines=[],
                    pages=[],
                    topics=[],
                )
            )

        opp_rows = list(
            self.db.scalars(
                select(CgSourceOpportunity)
                .where(CgSourceOpportunity.analysis_id == analysis_id)
                .order_by(CgSourceOpportunity.domain_answer_influence_pct.desc())
            ).all()
        )
        from citation_graph.opportunity import SourceOpportunity

        opportunities = [
            SourceOpportunity(
                cited_domain=o.cited_domain,
                source_class=o.source_class,
                opportunity_type=o.opportunity_type,
                priority=o.priority,
                domain_answer_influence_pct=o.domain_answer_influence_pct,
                client_mention_pct=o.client_mention_pct,
                top_competitor_name=o.top_competitor_name,
                top_competitor_mention_pct=o.top_competitor_mention_pct,
                title=o.title,
                rationale=o.rationale,
                recommended_actions=[
                    line[2:].strip() if line.startswith("- ") else line.strip()
                    for line in (o.recommended_actions or "").splitlines()
                    if line.strip()
                ],
                manipulative_spam_rejected=o.manipulative_spam_rejected,
                forbidden_tactics_note=o.forbidden_tactics_note
                or "Manipulative spam rejected.",
            )
            for o in opp_rows
        ]

        pathway_rows = list(
            self.db.scalars(
                select(CgPathway)
                .where(CgPathway.analysis_id == analysis_id)
                .limit(100)
            ).all()
        )
        pathways = [
            PathwayView(
                engine_code=p.engine_code,
                prompt_fingerprint=p.prompt_fingerprint,
                answer_id=p.answer_id,
                cited_url=p.cited_url,
                cited_domain=p.cited_domain,
                page_path=p.page_path,
                entity_name=p.entity_name,
                topic_label=p.topic_label,
                source_class=p.source_class,
                pathway_key=p.pathway_key,
            )
            for p in pathway_rows
        ]

        class_counts = Counter(p.source_class for p in pathway_rows)
        return CitationGraphReport(
            analysis_id=analysis.id,
            topic_cluster=analysis.topic_cluster,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            observation_count=analysis.observation_count,
            citation_count=analysis.citation_count,
            domain_count=analysis.domain_count,
            pathway_count=analysis.pathway_count,
            domains=domains,
            hubs=[d for d in domains if d.is_citation_hub],
            pathways_sample=pathways,
            opportunities=opportunities,
            source_class_breakdown=dict(class_counts),
            cis_weights=dict(DEFAULT_CIS_WEIGHTS),
            manipulative_spam_rejected=True,
        )

    @staticmethod
    def pathway_chain() -> tuple[str, ...]:
        return PATHWAY_NODE_KINDS

    def _resolve_entities(
        self, obs: ObservationSpec, spec: CitationGraphSpec
    ) -> list[EntityMentionSpec]:
        if obs.entities:
            return list(obs.entities)
        text = (obs.answer_excerpt or "").lower()
        out: list[EntityMentionSpec] = []
        client = spec.client_brand.strip()
        if client:
            out.append(
                EntityMentionSpec(
                    entity_name=client,
                    mentioned=client.lower() in text,
                    is_client=True,
                )
            )
        for name in spec.competitor_brands:
            key = name.strip()
            if not key:
                continue
            out.append(
                EntityMentionSpec(
                    entity_name=key,
                    mentioned=key.lower() in text,
                    is_competitor=True,
                )
            )
        return out

    def _resolve_citations(
        self, obs: ObservationSpec, spec: CitationGraphSpec
    ) -> list[CitationSpec]:
        _ = spec
        if obs.citations:
            return list(obs.citations)
        urls = extract_urls(obs.answer_excerpt or "")
        return [
            CitationSpec(cited_url=url, prominence=max(0.35, 1.0 - 0.1 * idx), position_in_answer=idx + 1)
            for idx, url in enumerate(urls)
        ]
