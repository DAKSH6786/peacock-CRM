"""Persist and hydrate the Peacock Evidence Ledger graph."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from db_models.base import new_uuid
from db_models.evidence_ledger import (
    EVIDENCE_TYPES,
    LedgerAction,
    LedgerActionOutcomeLink,
    LedgerClaimEvidenceLink,
    LedgerEvidence,
    LedgerEvidenceFindingLink,
    LedgerFinding,
    LedgerFindingRecommendationLink,
    LedgerOutcome,
    LedgerRecommendation,
    LedgerRecommendationActionLink,
)
from evidence_ledger.models import (
    ClaimEvidencePointer,
    EvidenceGraph,
    EvidenceGraphEdge,
    EvidenceType,
    LedgerActionNode,
    LedgerEvidenceNode,
    LedgerFindingNode,
    LedgerOutcomeNode,
    LedgerRecommendationNode,
    SupportingValue,
)


def compute_freshness(
    observed_at: datetime,
    *,
    now: datetime | None = None,
    half_life_hours: float = 168.0,
) -> tuple[float, float]:
    """Return (freshness_hours, freshness_score in 0–1) from observation time."""
    current = now or datetime.now(UTC)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    hours = max(0.0, (current - observed_at).total_seconds() / 3600.0)
    # Exponential decay with configurable half-life (default 7 days)
    score = 0.5 ** (hours / half_life_hours) if half_life_hours > 0 else 0.0
    return hours, max(0.0, min(1.0, score))


class EvidenceLedgerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record_evidence(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        node: LedgerEvidenceNode,
    ) -> LedgerEvidenceNode:
        evidence_type = str(node.evidence_type)
        if evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"Unsupported evidence_type: {evidence_type}")

        hours, score = compute_freshness(node.observed_at)
        if node.freshness_hours or node.freshness_score != 1.0:
            hours = node.freshness_hours
            score = node.freshness_score

        row = LedgerEvidence(
            id=node.id or new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            code=node.code or f"ev.{evidence_type.lower()}.{new_uuid()[:8]}",
            evidence_type=evidence_type,
            source=node.source,
            observed_at=node.observed_at,
            freshness_hours=hours,
            freshness_score=score,
            confidence=node.confidence,
            scope_kind=node.scope_kind,
            scope_ref=node.scope_ref,
            value_text=node.supporting_value.text,
            value_number=node.supporting_value.number,
            value_bool=node.supporting_value.boolean,
            value_unit=node.supporting_value.unit,
            summary=node.summary,
            source_url=node.source_url,
            website_id=node.website_id,
            crawl_id=node.crawl_id,
            intelligence_case_id=node.intelligence_case_id,
        )
        self.session.add(row)
        self.session.commit()
        return self._evidence_to_node(row)

    def record_finding(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        node: LedgerFindingNode,
        evidence_ids: list[str] | None = None,
        link_role: str = "supports",
    ) -> LedgerFindingNode:
        row = LedgerFinding(
            id=node.id or new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            code=node.code or f"finding.{new_uuid()[:8]}",
            statement=node.statement,
            summary=node.summary,
            confidence=node.confidence,
            finding_kind=node.finding_kind,
            agent_name=node.agent_name,
            is_llm_derived=node.is_llm_derived,
            severity=node.severity,
            website_id=node.website_id,
            intelligence_case_id=node.intelligence_case_id,
        )
        self.session.add(row)
        self.session.flush()
        for evidence_id in evidence_ids or node.evidence_ids:
            self.session.add(
                LedgerEvidenceFindingLink(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    evidence_id=evidence_id,
                    finding_id=row.id,
                    role=link_role,
                )
            )
        self.session.commit()
        return self.get_finding(row.id)  # type: ignore[return-value]

    def record_recommendation(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        node: LedgerRecommendationNode,
        finding_ids: list[str] | None = None,
        link_role: str = "motivates",
    ) -> LedgerRecommendationNode:
        row = LedgerRecommendation(
            id=node.id or new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            code=node.code or f"rec.{new_uuid()[:8]}",
            title=node.title,
            rationale=node.rationale,
            priority=node.priority,
            impact=node.impact,
            effort=node.effort,
            confidence=node.confidence,
            priority_score=node.priority_score,
            suggested_fix=node.suggested_fix,
            website_id=node.website_id,
            central_recommendation_id=node.central_recommendation_id,
            intelligence_case_id=node.intelligence_case_id,
        )
        self.session.add(row)
        self.session.flush()
        for finding_id in finding_ids or node.finding_ids:
            self.session.add(
                LedgerFindingRecommendationLink(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    finding_id=finding_id,
                    recommendation_id=row.id,
                    role=link_role,
                )
            )
        self.session.commit()
        return self.get_recommendation(row.id)  # type: ignore[return-value]

    def record_action(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        node: LedgerActionNode,
        recommendation_ids: list[str] | None = None,
        link_role: str = "implements",
    ) -> LedgerActionNode:
        row = LedgerAction(
            id=node.id or new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            code=node.code or f"action.{new_uuid()[:8]}",
            title=node.title,
            description=node.description,
            owner_role=node.owner_role,
            success_metric=node.success_metric,
            action_status=node.action_status,
            due_at=node.due_at,
            started_at=node.started_at,
            completed_at=node.completed_at,
            website_id=node.website_id,
            roadmap_task_id=node.roadmap_task_id,
            execution_id=node.execution_id,
        )
        self.session.add(row)
        self.session.flush()
        for recommendation_id in recommendation_ids or node.recommendation_ids:
            self.session.add(
                LedgerRecommendationActionLink(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    recommendation_id=recommendation_id,
                    action_id=row.id,
                    role=link_role,
                )
            )
        self.session.commit()
        return self.get_action(row.id)  # type: ignore[return-value]

    def record_outcome(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        node: LedgerOutcomeNode,
        action_ids: list[str] | None = None,
        link_role: str = "measures",
    ) -> LedgerOutcomeNode:
        row = LedgerOutcome(
            id=node.id or new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            code=node.code or f"outcome.{new_uuid()[:8]}",
            metric_key=node.metric_key,
            metric_value=node.metric_value,
            baseline_value=node.baseline_value,
            target_value=node.target_value,
            observed_at=node.observed_at,
            notes=node.notes,
            outcome_kind=node.outcome_kind,
            website_id=node.website_id,
            central_outcome_id=node.central_outcome_id,
        )
        self.session.add(row)
        self.session.flush()
        for action_id in action_ids or node.action_ids:
            self.session.add(
                LedgerActionOutcomeLink(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    action_id=action_id,
                    outcome_id=row.id,
                    role=link_role,
                )
            )
        self.session.commit()
        return self.get_outcome(row.id)  # type: ignore[return-value]

    def link_claim_to_evidence(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        pointer: ClaimEvidencePointer,
    ) -> ClaimEvidencePointer:
        row = LedgerClaimEvidenceLink(
            id=pointer.id or new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            claim_kind=pointer.claim_kind,
            claim_ref=pointer.claim_ref,
            claim_text=pointer.claim_text,
            evidence_id=pointer.evidence_id,
            role=pointer.role,
            confidence=pointer.confidence,
        )
        self.session.add(row)
        self.session.commit()
        return ClaimEvidencePointer(
            id=row.id,
            claim_kind=row.claim_kind,
            claim_ref=row.claim_ref,
            claim_text=row.claim_text,
            evidence_id=row.evidence_id,
            role=row.role,
            confidence=row.confidence,
        )

    def get_evidence(self, evidence_id: str) -> LedgerEvidenceNode | None:
        row = self.session.get(LedgerEvidence, evidence_id)
        return self._evidence_to_node(row) if row else None

    def get_finding(self, finding_id: str) -> LedgerFindingNode | None:
        row = self.session.get(
            LedgerFinding,
            finding_id,
            options=(selectinload(LedgerFinding.evidence_links),),
        )
        if row is None:
            return None
        return LedgerFindingNode(
            id=row.id,
            code=row.code,
            statement=row.statement,
            summary=row.summary,
            confidence=row.confidence,
            finding_kind=row.finding_kind,
            agent_name=row.agent_name,
            is_llm_derived=row.is_llm_derived,
            severity=row.severity,
            website_id=row.website_id,
            intelligence_case_id=row.intelligence_case_id,
            evidence_ids=[link.evidence_id for link in row.evidence_links],
        )

    def get_recommendation(self, recommendation_id: str) -> LedgerRecommendationNode | None:
        row = self.session.get(
            LedgerRecommendation,
            recommendation_id,
            options=(selectinload(LedgerRecommendation.finding_links),),
        )
        if row is None:
            return None
        return LedgerRecommendationNode(
            id=row.id,
            code=row.code,
            title=row.title,
            rationale=row.rationale,
            priority=row.priority,
            impact=row.impact,
            effort=row.effort,
            confidence=row.confidence,
            priority_score=row.priority_score,
            suggested_fix=row.suggested_fix,
            website_id=row.website_id,
            central_recommendation_id=row.central_recommendation_id,
            intelligence_case_id=row.intelligence_case_id,
            finding_ids=[link.finding_id for link in row.finding_links],
        )

    def get_action(self, action_id: str) -> LedgerActionNode | None:
        row = self.session.get(
            LedgerAction,
            action_id,
            options=(selectinload(LedgerAction.recommendation_links),),
        )
        if row is None:
            return None
        return LedgerActionNode(
            id=row.id,
            code=row.code,
            title=row.title,
            description=row.description,
            owner_role=row.owner_role,
            success_metric=row.success_metric,
            action_status=row.action_status,
            due_at=row.due_at,
            started_at=row.started_at,
            completed_at=row.completed_at,
            website_id=row.website_id,
            roadmap_task_id=row.roadmap_task_id,
            execution_id=row.execution_id,
            recommendation_ids=[link.recommendation_id for link in row.recommendation_links],
        )

    def get_outcome(self, outcome_id: str) -> LedgerOutcomeNode | None:
        row = self.session.get(
            LedgerOutcome,
            outcome_id,
            options=(selectinload(LedgerOutcome.action_links),),
        )
        if row is None:
            return None
        return LedgerOutcomeNode(
            id=row.id,
            code=row.code,
            metric_key=row.metric_key,
            metric_value=row.metric_value,
            baseline_value=row.baseline_value,
            target_value=row.target_value,
            observed_at=row.observed_at,
            notes=row.notes,
            outcome_kind=row.outcome_kind,
            website_id=row.website_id,
            central_outcome_id=row.central_outcome_id,
            action_ids=[link.action_id for link in row.action_links],
        )

    def get_graph_for_workspace(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        limit: int = 200,
    ) -> EvidenceGraph:
        evidences = list(
            self.session.scalars(
                select(LedgerEvidence)
                .where(
                    LedgerEvidence.organisation_id == organisation_id,
                    LedgerEvidence.workspace_id == workspace_id,
                    LedgerEvidence.status == "active",
                )
                .order_by(LedgerEvidence.observed_at.desc())
                .limit(limit)
            )
        )
        findings = list(
            self.session.scalars(
                select(LedgerFinding)
                .where(
                    LedgerFinding.organisation_id == organisation_id,
                    LedgerFinding.workspace_id == workspace_id,
                    LedgerFinding.status == "active",
                )
                .options(selectinload(LedgerFinding.evidence_links))
                .limit(limit)
            )
        )
        recommendations = list(
            self.session.scalars(
                select(LedgerRecommendation)
                .where(
                    LedgerRecommendation.organisation_id == organisation_id,
                    LedgerRecommendation.workspace_id == workspace_id,
                    LedgerRecommendation.status == "active",
                )
                .options(selectinload(LedgerRecommendation.finding_links))
                .limit(limit)
            )
        )
        actions = list(
            self.session.scalars(
                select(LedgerAction)
                .where(
                    LedgerAction.organisation_id == organisation_id,
                    LedgerAction.workspace_id == workspace_id,
                    LedgerAction.status == "active",
                )
                .options(selectinload(LedgerAction.recommendation_links))
                .limit(limit)
            )
        )
        outcomes = list(
            self.session.scalars(
                select(LedgerOutcome)
                .where(
                    LedgerOutcome.organisation_id == organisation_id,
                    LedgerOutcome.workspace_id == workspace_id,
                    LedgerOutcome.status == "active",
                )
                .options(selectinload(LedgerOutcome.action_links))
                .limit(limit)
            )
        )
        claim_rows = list(
            self.session.scalars(
                select(LedgerClaimEvidenceLink)
                .where(
                    LedgerClaimEvidenceLink.organisation_id == organisation_id,
                    LedgerClaimEvidenceLink.workspace_id == workspace_id,
                    LedgerClaimEvidenceLink.status == "active",
                )
                .limit(limit)
            )
        )

        edges: list[EvidenceGraphEdge] = []
        for finding in findings:
            for link in finding.evidence_links:
                edges.append(
                    EvidenceGraphEdge(
                        from_kind="evidence",
                        from_id=link.evidence_id,
                        to_kind="finding",
                        to_id=finding.id,
                        role=link.role,
                        weight=link.weight,
                    )
                )
        for rec in recommendations:
            for link in rec.finding_links:
                edges.append(
                    EvidenceGraphEdge(
                        from_kind="finding",
                        from_id=link.finding_id,
                        to_kind="recommendation",
                        to_id=rec.id,
                        role=link.role,
                        weight=link.weight,
                    )
                )
        for action in actions:
            for link in action.recommendation_links:
                edges.append(
                    EvidenceGraphEdge(
                        from_kind="recommendation",
                        from_id=link.recommendation_id,
                        to_kind="action",
                        to_id=action.id,
                        role=link.role,
                        weight=link.weight,
                    )
                )
        for outcome in outcomes:
            for link in outcome.action_links:
                edges.append(
                    EvidenceGraphEdge(
                        from_kind="action",
                        from_id=link.action_id,
                        to_kind="outcome",
                        to_id=outcome.id,
                        role=link.role,
                        weight=link.weight,
                    )
                )

        return EvidenceGraph(
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            evidences=[self._evidence_to_node(row) for row in evidences],
            findings=[
                LedgerFindingNode(
                    id=row.id,
                    code=row.code,
                    statement=row.statement,
                    summary=row.summary,
                    confidence=row.confidence,
                    finding_kind=row.finding_kind,
                    agent_name=row.agent_name,
                    is_llm_derived=row.is_llm_derived,
                    severity=row.severity,
                    website_id=row.website_id,
                    intelligence_case_id=row.intelligence_case_id,
                    evidence_ids=[link.evidence_id for link in row.evidence_links],
                )
                for row in findings
            ],
            recommendations=[
                LedgerRecommendationNode(
                    id=row.id,
                    code=row.code,
                    title=row.title,
                    rationale=row.rationale,
                    priority=row.priority,
                    impact=row.impact,
                    effort=row.effort,
                    confidence=row.confidence,
                    priority_score=row.priority_score,
                    suggested_fix=row.suggested_fix,
                    website_id=row.website_id,
                    central_recommendation_id=row.central_recommendation_id,
                    intelligence_case_id=row.intelligence_case_id,
                    finding_ids=[link.finding_id for link in row.finding_links],
                )
                for row in recommendations
            ],
            actions=[
                LedgerActionNode(
                    id=row.id,
                    code=row.code,
                    title=row.title,
                    description=row.description,
                    owner_role=row.owner_role,
                    success_metric=row.success_metric,
                    action_status=row.action_status,
                    due_at=row.due_at,
                    started_at=row.started_at,
                    completed_at=row.completed_at,
                    website_id=row.website_id,
                    roadmap_task_id=row.roadmap_task_id,
                    execution_id=row.execution_id,
                    recommendation_ids=[link.recommendation_id for link in row.recommendation_links],
                )
                for row in actions
            ],
            outcomes=[
                LedgerOutcomeNode(
                    id=row.id,
                    code=row.code,
                    metric_key=row.metric_key,
                    metric_value=row.metric_value,
                    baseline_value=row.baseline_value,
                    target_value=row.target_value,
                    observed_at=row.observed_at,
                    notes=row.notes,
                    outcome_kind=row.outcome_kind,
                    website_id=row.website_id,
                    central_outcome_id=row.central_outcome_id,
                    action_ids=[link.action_id for link in row.action_links],
                )
                for row in outcomes
            ],
            edges=edges,
            claim_pointers=[
                ClaimEvidencePointer(
                    id=row.id,
                    claim_kind=row.claim_kind,
                    claim_ref=row.claim_ref,
                    claim_text=row.claim_text,
                    evidence_id=row.evidence_id,
                    role=row.role,
                    confidence=row.confidence,
                )
                for row in claim_rows
            ],
        )

    def trace_from_evidence(self, evidence_id: str) -> EvidenceGraph | None:
        """Follow Evidence → Finding → Recommendation → Action → Outcome."""
        evidence = self.session.get(
            LedgerEvidence,
            evidence_id,
            options=(selectinload(LedgerEvidence.finding_links),),
        )
        if evidence is None:
            return None

        finding_ids = [link.finding_id for link in evidence.finding_links]
        findings = list(
            self.session.scalars(
                select(LedgerFinding)
                .where(LedgerFinding.id.in_(finding_ids))
                .options(
                    selectinload(LedgerFinding.evidence_links),
                    selectinload(LedgerFinding.recommendation_links),
                )
            )
        ) if finding_ids else []

        rec_ids = [link.recommendation_id for f in findings for link in f.recommendation_links]
        recommendations = list(
            self.session.scalars(
                select(LedgerRecommendation)
                .where(LedgerRecommendation.id.in_(rec_ids))
                .options(
                    selectinload(LedgerRecommendation.finding_links),
                    selectinload(LedgerRecommendation.action_links),
                )
            )
        ) if rec_ids else []

        action_ids = [link.action_id for r in recommendations for link in r.action_links]
        actions = list(
            self.session.scalars(
                select(LedgerAction)
                .where(LedgerAction.id.in_(action_ids))
                .options(
                    selectinload(LedgerAction.recommendation_links),
                    selectinload(LedgerAction.outcome_links),
                )
            )
        ) if action_ids else []

        outcome_ids = [link.outcome_id for a in actions for link in a.outcome_links]
        outcomes = list(
            self.session.scalars(
                select(LedgerOutcome)
                .where(LedgerOutcome.id.in_(outcome_ids))
                .options(selectinload(LedgerOutcome.action_links))
            )
        ) if outcome_ids else []

        graph = EvidenceGraph(
            organisation_id=evidence.organisation_id,
            workspace_id=evidence.workspace_id,
            evidences=[self._evidence_to_node(evidence)],
        )
        edges: list[EvidenceGraphEdge] = []
        for finding in findings:
            for link in finding.evidence_links:
                if link.evidence_id == evidence.id:
                    edges.append(
                        EvidenceGraphEdge(
                            from_kind="evidence",
                            from_id=evidence.id,
                            to_kind="finding",
                            to_id=finding.id,
                            role=link.role,
                            weight=link.weight,
                        )
                    )
            graph.findings.append(
                LedgerFindingNode(
                    id=finding.id,
                    code=finding.code,
                    statement=finding.statement,
                    summary=finding.summary,
                    confidence=finding.confidence,
                    finding_kind=finding.finding_kind,
                    agent_name=finding.agent_name,
                    is_llm_derived=finding.is_llm_derived,
                    severity=finding.severity,
                    website_id=finding.website_id,
                    intelligence_case_id=finding.intelligence_case_id,
                    evidence_ids=[link.evidence_id for link in finding.evidence_links],
                )
            )
        for rec in recommendations:
            for link in rec.finding_links:
                edges.append(
                    EvidenceGraphEdge(
                        from_kind="finding",
                        from_id=link.finding_id,
                        to_kind="recommendation",
                        to_id=rec.id,
                        role=link.role,
                        weight=link.weight,
                    )
                )
            graph.recommendations.append(
                LedgerRecommendationNode(
                    id=rec.id,
                    code=rec.code,
                    title=rec.title,
                    rationale=rec.rationale,
                    priority=rec.priority,
                    impact=rec.impact,
                    effort=rec.effort,
                    confidence=rec.confidence,
                    priority_score=rec.priority_score,
                    suggested_fix=rec.suggested_fix,
                    website_id=rec.website_id,
                    central_recommendation_id=rec.central_recommendation_id,
                    intelligence_case_id=rec.intelligence_case_id,
                    finding_ids=[link.finding_id for link in rec.finding_links],
                )
            )
        for action in actions:
            for link in action.recommendation_links:
                edges.append(
                    EvidenceGraphEdge(
                        from_kind="recommendation",
                        from_id=link.recommendation_id,
                        to_kind="action",
                        to_id=action.id,
                        role=link.role,
                        weight=link.weight,
                    )
                )
            graph.actions.append(
                LedgerActionNode(
                    id=action.id,
                    code=action.code,
                    title=action.title,
                    description=action.description,
                    owner_role=action.owner_role,
                    success_metric=action.success_metric,
                    action_status=action.action_status,
                    due_at=action.due_at,
                    started_at=action.started_at,
                    completed_at=action.completed_at,
                    website_id=action.website_id,
                    roadmap_task_id=action.roadmap_task_id,
                    execution_id=action.execution_id,
                    recommendation_ids=[link.recommendation_id for link in action.recommendation_links],
                )
            )
        for outcome in outcomes:
            for link in outcome.action_links:
                edges.append(
                    EvidenceGraphEdge(
                        from_kind="action",
                        from_id=link.action_id,
                        to_kind="outcome",
                        to_id=outcome.id,
                        role=link.role,
                        weight=link.weight,
                    )
                )
            graph.outcomes.append(
                LedgerOutcomeNode(
                    id=outcome.id,
                    code=outcome.code,
                    metric_key=outcome.metric_key,
                    metric_value=outcome.metric_value,
                    baseline_value=outcome.baseline_value,
                    target_value=outcome.target_value,
                    observed_at=outcome.observed_at,
                    notes=outcome.notes,
                    outcome_kind=outcome.outcome_kind,
                    website_id=outcome.website_id,
                    central_outcome_id=outcome.central_outcome_id,
                    action_ids=[link.action_id for link in outcome.action_links],
                )
            )
        graph.edges = edges
        return graph

    @staticmethod
    def _evidence_to_node(row: LedgerEvidence) -> LedgerEvidenceNode:
        try:
            evidence_type: EvidenceType | str = EvidenceType(row.evidence_type)
        except ValueError:
            evidence_type = row.evidence_type
        return LedgerEvidenceNode(
            id=row.id,
            code=row.code,
            evidence_type=evidence_type,
            source=row.source,
            observed_at=row.observed_at,
            freshness_hours=row.freshness_hours,
            freshness_score=row.freshness_score,
            confidence=row.confidence,
            scope_kind=row.scope_kind,
            scope_ref=row.scope_ref,
            supporting_value=SupportingValue(
                text=row.value_text,
                number=row.value_number,
                boolean=row.value_bool,
                unit=row.value_unit,
            ),
            summary=row.summary,
            source_url=row.source_url,
            website_id=row.website_id,
            crawl_id=row.crawl_id,
            intelligence_case_id=row.intelligence_case_id,
        )
