"""Peacock Council 2.0 orchestration — opposing-role debate sessions."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from council2.debate import (
    AgentAssignment,
    ClaimArtifact,
    CouncilDebateResult,
    CounterargumentArtifact,
    DecisionArtifact,
    DisagreementArtifact,
    EvidenceArtifact,
    EvidenceRequestArtifact,
    RoundRecord,
    run_council_debate,
)
from council2.models import Council2Report, Council2Spec
from db_models.base import new_uuid
from db_models.council2 import (
    METHODOLOGY,
    STORED_ARTIFACT_KINDS,
    C2Agent,
    C2Claim,
    C2Counterargument,
    C2Decision,
    C2Disagreement,
    C2Evidence,
    C2EvidenceRequest,
    C2RoundRecord,
    Council2Session,
)


class Council2Service:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_session(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: Council2Spec,
        created_by: str | None = None,
    ) -> Council2Report:
        result = run_council_debate(spec.brief)

        session = Council2Session(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.brief.client_brand.strip(),
            decision_question=spec.brief.decision_question.strip(),
            context_summary=spec.brief.context_summary,
            session_status="completed",
            methodology=METHODOLOGY,
            open_opinion_prompts_rejected=True,
            chain_of_thought_not_stored=True,
            stored_artifact_kinds=",".join(STORED_ARTIFACT_KINDS),
            round_count=5,
            final_decision_text=result.final_decision,
            final_confidence=result.final_confidence,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(session)
        self.db.flush()

        for agent in result.agents:
            self.db.add(
                C2Agent(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    session_id=session.id,
                    role_code=agent.role_code,
                    role_mandate=agent.role_mandate,
                    model_label=agent.model_label,
                    open_opinion_prompt_rejected=True,
                )
            )

        for rnd in result.rounds:
            self.db.add(
                C2RoundRecord(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    session_id=session.id,
                    round_number=rnd.round_number,
                    round_code=rnd.round_code,
                    round_label=rnd.round_label,
                    structured_summary=rnd.structured_summary,
                )
            )

        for claim in result.claims:
            self.db.add(
                C2Claim(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    session_id=session.id,
                    claim_key=claim.claim_key,
                    role_code=claim.role_code,
                    round_number=claim.round_number,
                    statement=claim.statement,
                    confidence=claim.confidence,
                    stance=claim.stance,
                )
            )

        for ev in result.evidence:
            self.db.add(
                C2Evidence(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    session_id=session.id,
                    claim_key=ev.claim_key,
                    role_code=ev.role_code,
                    round_number=ev.round_number,
                    statement=ev.statement,
                    source_ref=ev.source_ref,
                    strength=ev.strength,
                )
            )

        for ca in result.counterarguments:
            self.db.add(
                C2Counterargument(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    session_id=session.id,
                    claim_key=ca.claim_key,
                    role_code=ca.role_code,
                    round_number=ca.round_number,
                    statement=ca.statement,
                    confidence=ca.confidence,
                )
            )

        for d in result.disagreements:
            self.db.add(
                C2Disagreement(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    session_id=session.id,
                    claim_key=d.claim_key,
                    role_a=d.role_a,
                    role_b=d.role_b,
                    summary=d.summary,
                    severity=d.severity,
                )
            )

        for req in result.evidence_requests:
            self.db.add(
                C2EvidenceRequest(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    session_id=session.id,
                    claim_key=req.claim_key,
                    requested_by_role=req.requested_by_role,
                    request_statement=req.request_statement,
                    fulfilled=req.fulfilled,
                    fulfillment_evidence=req.fulfillment_evidence,
                )
            )

        for dec in result.decisions:
            self.db.add(
                C2Decision(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    session_id=session.id,
                    decision=dec.decision,
                    confidence=dec.confidence,
                    supporting_claim_keys=",".join(dec.supporting_claim_keys),
                    rejected_claim_keys=",".join(dec.rejected_claim_keys),
                    judge_role=dec.judge_role,
                )
            )

        self.db.commit()
        return Council2Report(
            session_id=session.id,
            name=session.name,
            client_brand=session.client_brand,
            methodology=session.methodology,
            result=result,
        )

    def get_session(
        self, *, session_id: str, organisation_id: str
    ) -> Council2Report | None:
        session = self.db.scalar(
            select(Council2Session).where(
                Council2Session.id == session_id,
                Council2Session.organisation_id == organisation_id,
            )
        )
        if session is None:
            return None

        agents = [
            AgentAssignment(
                role_code=a.role_code,
                role_mandate=a.role_mandate,
                model_label=a.model_label,
                open_opinion_prompt_rejected=a.open_opinion_prompt_rejected,
            )
            for a in self.db.scalars(
                select(C2Agent).where(C2Agent.session_id == session.id)
            ).all()
        ]
        rounds = [
            RoundRecord(
                round_number=r.round_number,
                round_code=r.round_code,
                round_label=r.round_label,
                structured_summary=r.structured_summary,
            )
            for r in self.db.scalars(
                select(C2RoundRecord)
                .where(C2RoundRecord.session_id == session.id)
                .order_by(C2RoundRecord.round_number.asc())
            ).all()
        ]
        claims = [
            ClaimArtifact(
                claim_key=c.claim_key,
                role_code=c.role_code,
                round_number=c.round_number,
                statement=c.statement,
                confidence=c.confidence,
                stance=c.stance,
            )
            for c in self.db.scalars(
                select(C2Claim).where(C2Claim.session_id == session.id)
            ).all()
        ]
        evidence = [
            EvidenceArtifact(
                claim_key=e.claim_key,
                role_code=e.role_code,
                round_number=e.round_number,
                statement=e.statement,
                source_ref=e.source_ref,
                strength=e.strength,
            )
            for e in self.db.scalars(
                select(C2Evidence).where(C2Evidence.session_id == session.id)
            ).all()
        ]
        counters = [
            CounterargumentArtifact(
                claim_key=c.claim_key,
                role_code=c.role_code,
                round_number=c.round_number,
                statement=c.statement,
                confidence=c.confidence,
            )
            for c in self.db.scalars(
                select(C2Counterargument).where(
                    C2Counterargument.session_id == session.id
                )
            ).all()
        ]
        disagreements = [
            DisagreementArtifact(
                claim_key=d.claim_key,
                role_a=d.role_a,
                role_b=d.role_b,
                summary=d.summary,
                severity=d.severity,
            )
            for d in self.db.scalars(
                select(C2Disagreement).where(C2Disagreement.session_id == session.id)
            ).all()
        ]
        requests = [
            EvidenceRequestArtifact(
                claim_key=r.claim_key,
                requested_by_role=r.requested_by_role,
                request_statement=r.request_statement,
                fulfilled=r.fulfilled,
                fulfillment_evidence=r.fulfillment_evidence,
            )
            for r in self.db.scalars(
                select(C2EvidenceRequest).where(
                    C2EvidenceRequest.session_id == session.id
                )
            ).all()
        ]
        decisions = [
            DecisionArtifact(
                decision=d.decision,
                confidence=d.confidence,
                supporting_claim_keys=[
                    x for x in (d.supporting_claim_keys or "").split(",") if x
                ],
                rejected_claim_keys=[
                    x for x in (d.rejected_claim_keys or "").split(",") if x
                ],
                judge_role=d.judge_role,
            )
            for d in self.db.scalars(
                select(C2Decision).where(C2Decision.session_id == session.id)
            ).all()
        ]

        from db_models.council2 import METHODOLOGY_NOTE

        result = CouncilDebateResult(
            decision_question=session.decision_question,
            agents=agents,
            rounds=rounds,
            claims=claims,
            evidence=evidence,
            counterarguments=counters,
            disagreements=disagreements,
            evidence_requests=requests,
            decisions=decisions,
            final_decision=session.final_decision_text or "",
            final_confidence=session.final_confidence or 0.0,
            open_opinion_prompts_rejected=session.open_opinion_prompts_rejected,
            chain_of_thought_not_stored=session.chain_of_thought_not_stored,
            stored_artifact_kinds=[
                x for x in (session.stored_artifact_kinds or "").split(",") if x
            ],
            methodology_note=METHODOLOGY_NOTE,
            summary=session.summary or "",
        )
        return Council2Report(
            session_id=session.id,
            name=session.name,
            client_brand=session.client_brand,
            methodology=session.methodology,
            result=result,
        )
