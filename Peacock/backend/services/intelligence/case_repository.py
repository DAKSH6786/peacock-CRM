"""Persist / hydrate PINE IntelligenceCase aggregates relationally."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session, selectinload

from db_models.base import new_uuid
from db_models.intelligence_case import (
    IntelligenceCaseAgentClaim,
    IntelligenceCaseAgentFinding,
    IntelligenceCaseAssumption,
    IntelligenceCaseContextItem,
    IntelligenceCaseContradiction,
    IntelligenceCaseEvidence,
    IntelligenceCaseEvidenceUrl,
    IntelligenceCaseHypothesis,
    IntelligenceCaseModelUsed,
    IntelligenceCaseObservation,
    IntelligenceCaseOpportunity,
    IntelligenceCaseRecommendation,
    IntelligenceCaseRecommendationEvidence,
    IntelligenceCaseRecord,
    IntelligenceCaseRisk,
    IntelligenceCaseToolUsed,
    IntelligenceCaseUnknown,
)
from intelligence.case import (
    CaseAgentFinding,
    CaseAssumption,
    CaseContextItem,
    CaseContradiction,
    CaseEvidence,
    CaseHypothesis,
    CaseModelUsed,
    CaseObservation,
    CaseOpportunity,
    CaseRecommendation,
    CaseRisk,
    CaseToolUsed,
    CaseUnknown,
    IntelligenceCase,
)


def _split_codes(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _join_codes(codes: list[str]) -> str | None:
    return ",".join(codes) if codes else None


class IntelligenceCaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, case: IntelligenceCase) -> IntelligenceCase:
        now = datetime.now(UTC)
        row = self.session.get(IntelligenceCaseRecord, case.case_id)
        if row is None:
            row = IntelligenceCaseRecord(
                id=case.case_id or new_uuid(),
                organisation_id=case.organisation_id,
                workspace_id=case.workspace_id,
                objective=case.objective,
                title=case.title,
                confidence=case.confidence,
                cost_usd_micros=case.cost_usd_micros,
                latency_ms=case.latency_ms,
                website_id=case.website_id,
                strategic_run_id=case.strategic_run_id,
                status=case.status,
                created_at=case.created_at or now,
                updated_at=now,
            )
            self.session.add(row)
            self.session.flush()
            case.case_id = row.id
        else:
            row.objective = case.objective
            row.title = case.title
            row.confidence = case.confidence
            row.cost_usd_micros = case.cost_usd_micros
            row.latency_ms = case.latency_ms
            row.website_id = case.website_id
            row.strategic_run_id = case.strategic_run_id
            row.status = case.status
            row.updated_at = now
            # Replace children for a clean snapshot write
            for collection in (
                row.context_items,
                row.observations,
                row.evidence_items,
                row.hypotheses,
                row.agent_findings,
                row.contradictions,
                row.unknowns,
                row.assumptions,
                row.risks,
                row.opportunities,
                row.recommendations,
                row.models_used,
                row.tools_used,
            ):
                collection.clear()
            self.session.flush()

        org = case.organisation_id
        ws = case.workspace_id
        case_id = row.id

        for index, item in enumerate(case.context):
            row.context_items.append(
                IntelligenceCaseContextItem(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    kind=item.kind,
                    key=item.key,
                    summary=item.summary,
                    relevance=item.relevance,
                    tokens_estimate=item.tokens_estimate,
                    source=item.source,
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.observations):
            row.observations.append(
                IntelligenceCaseObservation(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    code=item.code,
                    label=item.label,
                    detail=item.detail,
                    source=item.source,
                    observed_at=item.observed_at,
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.evidence):
            evidence = IntelligenceCaseEvidence(
                id=item.id or new_uuid(),
                organisation_id=org,
                workspace_id=ws,
                case_id=case_id,
                code=item.code,
                label=item.label,
                value_text=item.value_text,
                value_number=item.value_number,
                value_bool=item.value_bool,
                kind=item.kind,
                source=item.source,
                confidence=item.confidence,
                unit=item.unit,
                sort_order=index,
            )
            for url in item.related_urls:
                evidence.related_urls.append(
                    IntelligenceCaseEvidenceUrl(
                        id=new_uuid(),
                        organisation_id=org,
                        workspace_id=ws,
                        case_id=case_id,
                        evidence_id=evidence.id,
                        url=url,
                    )
                )
            row.evidence_items.append(evidence)

        for index, item in enumerate(case.hypotheses):
            row.hypotheses.append(
                IntelligenceCaseHypothesis(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    statement=item.statement,
                    confidence=item.confidence,
                    status_label=item.status_label,
                    supporting_evidence_codes=_join_codes(item.supporting_evidence_codes),
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.agent_findings):
            finding = IntelligenceCaseAgentFinding(
                id=item.id or new_uuid(),
                organisation_id=org,
                workspace_id=ws,
                case_id=case_id,
                agent_name=item.agent_name,
                role=item.role,
                summary=item.summary,
                confidence=item.confidence,
                is_llm_derived=item.is_llm_derived,
                sort_order=index,
            )
            for claim_index, claim in enumerate(item.claims):
                finding.claims.append(
                    IntelligenceCaseAgentClaim(
                        id=new_uuid(),
                        organisation_id=org,
                        workspace_id=ws,
                        case_id=case_id,
                        finding_id=finding.id,
                        claim=claim,
                        sort_order=claim_index,
                    )
                )
            row.agent_findings.append(finding)

        for index, item in enumerate(case.contradictions):
            row.contradictions.append(
                IntelligenceCaseContradiction(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    claim=item.claim,
                    challenge=item.challenge,
                    severity=item.severity,
                    unresolved=item.unresolved,
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.unknowns):
            row.unknowns.append(
                IntelligenceCaseUnknown(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    question=item.question,
                    impact_if_unknown=item.impact_if_unknown,
                    suggested_investigation=item.suggested_investigation,
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.assumptions):
            row.assumptions.append(
                IntelligenceCaseAssumption(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    statement=item.statement,
                    confidence=item.confidence,
                    risk_if_wrong=item.risk_if_wrong,
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.risks):
            row.risks.append(
                IntelligenceCaseRisk(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    title=item.title,
                    description=item.description,
                    severity=item.severity,
                    likelihood=item.likelihood,
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.opportunities):
            row.opportunities.append(
                IntelligenceCaseOpportunity(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    title=item.title,
                    description=item.description,
                    impact=item.impact,
                    effort=item.effort,
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.recommendations):
            rec = IntelligenceCaseRecommendation(
                id=item.id or new_uuid(),
                organisation_id=org,
                workspace_id=ws,
                case_id=case_id,
                title=item.title,
                rationale=item.rationale,
                priority=item.priority,
                impact=item.impact,
                effort=item.effort,
                confidence=item.confidence,
                priority_score=item.priority_score,
                depends_on_inference=item.depends_on_inference,
                suggested_fix=item.suggested_fix,
                sort_order=index,
            )
            for code in item.evidence_refs:
                rec.evidence_refs.append(
                    IntelligenceCaseRecommendationEvidence(
                        id=new_uuid(),
                        organisation_id=org,
                        workspace_id=ws,
                        case_id=case_id,
                        recommendation_id=rec.id,
                        evidence_code=code,
                    )
                )
            row.recommendations.append(rec)

        for index, item in enumerate(case.models_used):
            row.models_used.append(
                IntelligenceCaseModelUsed(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    provider_code=item.provider_code,
                    model_code=item.model_code,
                    role=item.role,
                    request_count=item.request_count,
                    cost_usd_micros=item.cost_usd_micros,
                    latency_ms=item.latency_ms,
                    sort_order=index,
                )
            )

        for index, item in enumerate(case.tools_used):
            row.tools_used.append(
                IntelligenceCaseToolUsed(
                    id=item.id or new_uuid(),
                    organisation_id=org,
                    workspace_id=ws,
                    case_id=case_id,
                    tool_name=item.tool_name,
                    tool_version=item.tool_version,
                    purpose=item.purpose,
                    invocation_count=item.invocation_count,
                    latency_ms=item.latency_ms,
                    sort_order=index,
                )
            )

        self.session.commit()
        return self.get(case_id)  # type: ignore[return-value]

    def get(self, case_id: str) -> IntelligenceCase | None:
        row = self.session.get(
            IntelligenceCaseRecord,
            case_id,
            options=(
                selectinload(IntelligenceCaseRecord.context_items),
                selectinload(IntelligenceCaseRecord.observations),
                selectinload(IntelligenceCaseRecord.evidence_items).selectinload(
                    IntelligenceCaseEvidence.related_urls
                ),
                selectinload(IntelligenceCaseRecord.hypotheses),
                selectinload(IntelligenceCaseRecord.agent_findings).selectinload(
                    IntelligenceCaseAgentFinding.claims
                ),
                selectinload(IntelligenceCaseRecord.contradictions),
                selectinload(IntelligenceCaseRecord.unknowns),
                selectinload(IntelligenceCaseRecord.assumptions),
                selectinload(IntelligenceCaseRecord.risks),
                selectinload(IntelligenceCaseRecord.opportunities),
                selectinload(IntelligenceCaseRecord.recommendations).selectinload(
                    IntelligenceCaseRecommendation.evidence_refs
                ),
                selectinload(IntelligenceCaseRecord.models_used),
                selectinload(IntelligenceCaseRecord.tools_used),
            ),
        )
        if row is None:
            return None
        return self._to_case(row)

    def _to_case(self, row: IntelligenceCaseRecord) -> IntelligenceCase:
        return IntelligenceCase(
            case_id=row.id,
            organisation_id=row.organisation_id,
            workspace_id=row.workspace_id,
            objective=row.objective,
            title=row.title,
            confidence=row.confidence,
            cost_usd_micros=row.cost_usd_micros,
            latency_ms=row.latency_ms,
            created_at=row.created_at,
            updated_at=row.updated_at,
            status=row.status,
            website_id=row.website_id,
            strategic_run_id=row.strategic_run_id,
            context=[
                CaseContextItem(
                    id=item.id,
                    kind=item.kind,
                    key=item.key,
                    summary=item.summary,
                    relevance=item.relevance,
                    tokens_estimate=item.tokens_estimate,
                    source=item.source,
                )
                for item in sorted(row.context_items, key=lambda x: x.sort_order)
            ],
            observations=[
                CaseObservation(
                    id=item.id,
                    code=item.code,
                    label=item.label,
                    detail=item.detail,
                    source=item.source,
                    observed_at=item.observed_at,
                )
                for item in sorted(row.observations, key=lambda x: x.sort_order)
            ],
            evidence=[
                CaseEvidence(
                    id=item.id,
                    code=item.code,
                    label=item.label,
                    kind=item.kind,  # type: ignore[arg-type]
                    source=item.source,
                    confidence=item.confidence,
                    value_text=item.value_text,
                    value_number=item.value_number,
                    value_bool=item.value_bool,
                    unit=item.unit,
                    related_urls=[url.url for url in item.related_urls],
                )
                for item in sorted(row.evidence_items, key=lambda x: x.sort_order)
            ],
            hypotheses=[
                CaseHypothesis(
                    id=item.id,
                    statement=item.statement,
                    confidence=item.confidence,
                    status_label=item.status_label,
                    supporting_evidence_codes=_split_codes(item.supporting_evidence_codes),
                )
                for item in sorted(row.hypotheses, key=lambda x: x.sort_order)
            ],
            agent_findings=[
                CaseAgentFinding(
                    id=item.id,
                    agent_name=item.agent_name,
                    role=item.role,
                    summary=item.summary,
                    confidence=item.confidence,
                    is_llm_derived=item.is_llm_derived,
                    claims=[
                        claim.claim
                        for claim in sorted(item.claims, key=lambda x: x.sort_order)
                    ],
                )
                for item in sorted(row.agent_findings, key=lambda x: x.sort_order)
            ],
            contradictions=[
                CaseContradiction(
                    id=item.id,
                    claim=item.claim,
                    challenge=item.challenge,
                    severity=item.severity,  # type: ignore[arg-type]
                    unresolved=item.unresolved,
                )
                for item in sorted(row.contradictions, key=lambda x: x.sort_order)
            ],
            unknowns=[
                CaseUnknown(
                    id=item.id,
                    question=item.question,
                    impact_if_unknown=item.impact_if_unknown,
                    suggested_investigation=item.suggested_investigation,
                )
                for item in sorted(row.unknowns, key=lambda x: x.sort_order)
            ],
            assumptions=[
                CaseAssumption(
                    id=item.id,
                    statement=item.statement,
                    confidence=item.confidence,
                    risk_if_wrong=item.risk_if_wrong,
                )
                for item in sorted(row.assumptions, key=lambda x: x.sort_order)
            ],
            risks=[
                CaseRisk(
                    id=item.id,
                    title=item.title,
                    description=item.description,
                    severity=item.severity,  # type: ignore[arg-type]
                    likelihood=item.likelihood,  # type: ignore[arg-type]
                )
                for item in sorted(row.risks, key=lambda x: x.sort_order)
            ],
            opportunities=[
                CaseOpportunity(
                    id=item.id,
                    title=item.title,
                    description=item.description,
                    impact=item.impact,
                    effort=item.effort,
                )
                for item in sorted(row.opportunities, key=lambda x: x.sort_order)
            ],
            recommendations=[
                CaseRecommendation(
                    id=item.id,
                    title=item.title,
                    rationale=item.rationale,
                    priority=item.priority,  # type: ignore[arg-type]
                    impact=item.impact,
                    effort=item.effort,
                    confidence=item.confidence,
                    priority_score=item.priority_score,
                    depends_on_inference=item.depends_on_inference,
                    suggested_fix=item.suggested_fix,
                    evidence_refs=[ref.evidence_code for ref in item.evidence_refs],
                )
                for item in sorted(row.recommendations, key=lambda x: x.sort_order)
            ],
            models_used=[
                CaseModelUsed(
                    id=item.id,
                    provider_code=item.provider_code,
                    model_code=item.model_code,
                    role=item.role,
                    request_count=item.request_count,
                    cost_usd_micros=item.cost_usd_micros,
                    latency_ms=item.latency_ms,
                )
                for item in sorted(row.models_used, key=lambda x: x.sort_order)
            ],
            tools_used=[
                CaseToolUsed(
                    id=item.id,
                    tool_name=item.tool_name,
                    tool_version=item.tool_version,
                    purpose=item.purpose,
                    invocation_count=item.invocation_count,
                    latency_ms=item.latency_ms,
                )
                for item in sorted(row.tools_used, key=lambda x: x.sort_order)
            ],
        )
