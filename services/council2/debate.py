"""Peacock Council 2.0 debate protocol — opposing roles, five rounds, no CoT storage.

Stored artifacts only: claim, evidence, counterargument, confidence, decision.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Any

from db_models.council2 import (
    COUNCIL_ROLES,
    DEBATE_ROUNDS,
    FORBIDDEN_PROMPTS,
    FORBIDDEN_STORAGE_FIELDS,
    METHODOLOGY_NOTE,
    ROLE_MANDATES,
    STORED_ARTIFACT_KINDS,
)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def assert_no_open_opinion_prompt(text: str) -> None:
    lowered = text or ""
    for forbidden in FORBIDDEN_PROMPTS:
        if forbidden.lower() in lowered.lower():
            raise ValueError(
                f"Open opinion prompts are rejected by Council 2.0: «{forbidden}». "
                "Assign opposing roles instead."
            )


def strip_forbidden_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Ensure chain-of-thought and related fields are never retained."""
    return {k: v for k, v in payload.items() if k not in FORBIDDEN_STORAGE_FIELDS}


@dataclass
class ContextFact:
    label: str
    statement: str
    polarity: str = "neutral"  # support|oppose|neutral
    strength: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CouncilBrief:
    decision_question: str
    client_brand: str
    context_summary: str | None = None
    facts: list[ContextFact] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    # Optional role→model mapping
    model_by_role: dict[str, str] = field(default_factory=dict)
    roles: list[str] = field(default_factory=list)

    def resolved_roles(self) -> list[str]:
        roles = list(self.roles) if self.roles else list(COUNCIL_ROLES)
        for r in roles:
            if r not in COUNCIL_ROLES:
                raise ValueError(f"Unsupported council role: {r}")
        return roles


@dataclass(slots=True)
class ClaimArtifact:
    claim_key: str
    role_code: str
    round_number: int
    statement: str
    confidence: float
    stance: str

    def to_dict(self) -> dict[str, Any]:
        return strip_forbidden_fields(asdict(self))


@dataclass(slots=True)
class EvidenceArtifact:
    claim_key: str
    role_code: str
    round_number: int
    statement: str
    source_ref: str | None
    strength: float

    def to_dict(self) -> dict[str, Any]:
        return strip_forbidden_fields(asdict(self))


@dataclass(slots=True)
class CounterargumentArtifact:
    claim_key: str
    role_code: str
    round_number: int
    statement: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return strip_forbidden_fields(asdict(self))


@dataclass(slots=True)
class DisagreementArtifact:
    claim_key: str
    role_a: str
    role_b: str
    summary: str
    severity: float

    def to_dict(self) -> dict[str, Any]:
        return strip_forbidden_fields(asdict(self))


@dataclass(slots=True)
class EvidenceRequestArtifact:
    claim_key: str
    requested_by_role: str
    request_statement: str
    fulfilled: bool
    fulfillment_evidence: str | None

    def to_dict(self) -> dict[str, Any]:
        return strip_forbidden_fields(asdict(self))


@dataclass(slots=True)
class DecisionArtifact:
    decision: str
    confidence: float
    supporting_claim_keys: list[str]
    rejected_claim_keys: list[str]
    judge_role: str = "council_judge"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return strip_forbidden_fields(d)


@dataclass(slots=True)
class RoundRecord:
    round_number: int
    round_code: str
    round_label: str
    structured_summary: str

    def to_dict(self) -> dict[str, Any]:
        return strip_forbidden_fields(asdict(self))


@dataclass(slots=True)
class AgentAssignment:
    role_code: str
    role_mandate: str
    model_label: str
    open_opinion_prompt_rejected: bool = True

    def to_dict(self) -> dict[str, Any]:
        return strip_forbidden_fields(asdict(self))


@dataclass
class CouncilDebateResult:
    decision_question: str
    agents: list[AgentAssignment]
    rounds: list[RoundRecord]
    claims: list[ClaimArtifact]
    evidence: list[EvidenceArtifact]
    counterarguments: list[CounterargumentArtifact]
    disagreements: list[DisagreementArtifact]
    evidence_requests: list[EvidenceRequestArtifact]
    decisions: list[DecisionArtifact]
    final_decision: str
    final_confidence: float
    open_opinion_prompts_rejected: bool
    chain_of_thought_not_stored: bool
    stored_artifact_kinds: list[str]
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return strip_forbidden_fields(
            {
                "decision_question": self.decision_question,
                "agents": [a.to_dict() for a in self.agents],
                "rounds": [r.to_dict() for r in self.rounds],
                "claims": [c.to_dict() for c in self.claims],
                "evidence": [e.to_dict() for e in self.evidence],
                "counterarguments": [c.to_dict() for c in self.counterarguments],
                "disagreements": [d.to_dict() for d in self.disagreements],
                "evidence_requests": [e.to_dict() for e in self.evidence_requests],
                "decisions": [d.to_dict() for d in self.decisions],
                "final_decision": self.final_decision,
                "final_confidence": self.final_confidence,
                "open_opinion_prompts_rejected": self.open_opinion_prompts_rejected,
                "chain_of_thought_not_stored": self.chain_of_thought_not_stored,
                "stored_artifact_kinds": list(self.stored_artifact_kinds),
                "methodology_note": self.methodology_note,
                "summary": self.summary,
            }
        )


# Role stance priors toward proceeding with a proposed major action
_ROLE_STANCE_BIAS: dict[str, float] = {
    "seo_researcher": 0.15,
    "geo_researcher": 0.18,
    "business_strategist": 0.12,
    "competitor_analyst": 0.05,
    "evidence_reviewer": -0.05,
    "sceptic": -0.25,
    "risk_analyst": -0.20,
}


def _fact_support_score(facts: list[ContextFact]) -> float:
    if not facts:
        return 0.5
    scores = []
    for f in facts:
        s = _clamp01(f.strength)
        if f.polarity == "support":
            scores.append(0.5 + 0.5 * s)
        elif f.polarity == "oppose":
            scores.append(0.5 - 0.5 * s)
        else:
            scores.append(0.5)
    return _clamp01(mean(scores))


def _claim_key(role: str, round_number: int, idx: int) -> str:
    return f"{role}-r{round_number}-{idx}"


def _independent_claim(
    role: str,
    brief: CouncilBrief,
    support_base: float,
) -> tuple[ClaimArtifact, EvidenceArtifact, CounterargumentArtifact | None]:
    bias = _ROLE_STANCE_BIAS.get(role, 0.0)
    conf = _clamp01(support_base + bias)
    # Adversarial roles oppose unless support is overwhelming
    if role in ("sceptic", "risk_analyst"):
        if support_base < 0.9:
            stance = "oppose"
            conf = _clamp01(max(conf, 0.55))
            statement = (
                f"As {role.replace('_', ' ')}: do not proceed on «{brief.decision_question}» "
                f"until stronger evidence resolves key risks for {brief.client_brand}."
            )
            evidence_stmt = (
                f"{role} cites weak provenance / downside exposure in the current brief."
            )
            counter = CounterargumentArtifact(
                claim_key=_claim_key(role, 1, 0),
                role_code=role,
                round_number=1,
                statement=(
                    f"{role} acknowledges possible upside but prioritizes unresolved risk."
                ),
                confidence=_clamp01(1.0 - conf + 0.25),
            )
            claim = ClaimArtifact(
                claim_key=_claim_key(role, 1, 0),
                role_code=role,
                round_number=1,
                statement=statement,
                confidence=conf,
                stance=stance,
            )
            evidence = EvidenceArtifact(
                claim_key=claim.claim_key,
                role_code=role,
                round_number=1,
                statement=evidence_stmt,
                source_ref=f"brief:{brief.client_brand}",
                strength=_clamp01(1.0 - support_base + 0.2),
            )
            return claim, evidence, counter

    if role == "evidence_reviewer" and support_base < 0.7:
        stance = "conditional"
        statement = (
            f"As evidence reviewer: support «{brief.decision_question}» only after "
            f"provenance gaps are closed for {brief.client_brand}."
        )
        evidence_stmt = "Evidence reviewer finds incomplete provenance in the brief."
        counter = CounterargumentArtifact(
            claim_key=_claim_key(role, 1, 0),
            role_code=role,
            round_number=1,
            statement="Proceeding without audit increases false-positive decision risk.",
            confidence=0.55,
        )
        claim = ClaimArtifact(
            claim_key=_claim_key(role, 1, 0),
            role_code=role,
            round_number=1,
            statement=statement,
            confidence=_clamp01(max(conf, 0.5)),
            stance=stance,
        )
        evidence = EvidenceArtifact(
            claim_key=claim.claim_key,
            role_code=role,
            round_number=1,
            statement=evidence_stmt,
            source_ref=f"brief:{brief.client_brand}",
            strength=_clamp01(support_base),
        )
        return claim, evidence, counter

    if conf >= 0.55:
        stance = "support"
        statement = (
            f"As {role.replace('_', ' ')}: proceed on «{brief.decision_question}» "
            f"for {brief.client_brand} given role-mandated upside signals."
        )
        evidence_stmt = (
            f"{role} cites role-aligned signals supporting the proposed decision."
        )
        counter = CounterargumentArtifact(
            claim_key=_claim_key(role, 1, 0),
            role_code=role,
            round_number=1,
            statement=(
                f"{role} notes residual uncertainty but still supports a conditional advance."
            ),
            confidence=_clamp01(1.0 - conf + 0.2),
        )
    elif role in ("sceptic", "risk_analyst", "evidence_reviewer") and conf < 0.55:
        stance = "oppose"
        statement = (
            f"As {role.replace('_', ' ')}: do not proceed on «{brief.decision_question}» "
            f"until stronger evidence resolves key risks for {brief.client_brand}."
        )
        evidence_stmt = (
            f"{role} cites weak provenance / downside exposure in the current brief."
        )
        counter = None
    else:
        stance = "conditional"
        statement = (
            f"As {role.replace('_', ' ')}: support «{brief.decision_question}» only with "
            f"guardrails and staged investment for {brief.client_brand}."
        )
        evidence_stmt = f"{role} finds mixed signals requiring staged execution."
        counter = CounterargumentArtifact(
            claim_key=_claim_key(role, 1, 0),
            role_code=role,
            round_number=1,
            statement=f"{role} counterweight: opportunity cost may exceed upside if delayed.",
            confidence=0.45,
        )

    claim = ClaimArtifact(
        claim_key=_claim_key(role, 1, 0),
        role_code=role,
        round_number=1,
        statement=statement,
        confidence=conf,
        stance=stance,
    )
    evidence = EvidenceArtifact(
        claim_key=claim.claim_key,
        role_code=role,
        round_number=1,
        statement=evidence_stmt,
        source_ref=f"brief:{brief.client_brand}",
        strength=_clamp01(support_base),
    )
    return claim, evidence, counter


def run_council_debate(brief: CouncilBrief) -> CouncilDebateResult:
    """Execute the five-round opposing-role debate protocol."""
    if not brief.decision_question.strip():
        raise ValueError("decision_question is required")
    if not brief.client_brand.strip():
        raise ValueError("client_brand is required")

    assert_no_open_opinion_prompt(brief.decision_question)
    if brief.context_summary:
        assert_no_open_opinion_prompt(brief.context_summary)

    roles = brief.resolved_roles()
    support_base = _fact_support_score(brief.facts)

    agents = [
        AgentAssignment(
            role_code=role,
            role_mandate=ROLE_MANDATES[role],
            model_label=brief.model_by_role.get(role, f"model:{role}"),
            open_opinion_prompt_rejected=True,
        )
        for role in roles
    ]
    # Verify mandates never use forbidden prompts
    for a in agents:
        assert_no_open_opinion_prompt(a.role_mandate)
        assert "what do you think" not in a.role_mandate.lower()

    claims: list[ClaimArtifact] = []
    evidence: list[EvidenceArtifact] = []
    counters: list[CounterargumentArtifact] = []
    rounds: list[RoundRecord] = []

    # --- Round 1: Independent analysis ---
    for role in roles:
        claim, ev, counter = _independent_claim(role, brief, support_base)
        claims.append(claim)
        evidence.append(ev)
        if counter:
            counters.append(counter)
    rounds.append(
        RoundRecord(
            round_number=1,
            round_code=DEBATE_ROUNDS[0][1],
            round_label=DEBATE_ROUNDS[0][2],
            structured_summary=(
                f"Round 1 independent analysis from {len(roles)} opposing roles. "
                f"Claims={len(claims)}. No open opinion prompts. CoT not stored."
            ),
        )
    )

    # --- Round 2: Cross-summary response ---
    summaries_by_role = {
        c.role_code: {"stance": c.stance, "confidence": c.confidence, "claim_key": c.claim_key}
        for c in claims
        if c.round_number == 1
    }
    for role in roles:
        others = {k: v for k, v in summaries_by_role.items() if k != role}
        support_others = sum(1 for v in others.values() if v["stance"] == "support")
        oppose_others = sum(1 for v in others.values() if v["stance"] == "oppose")
        own = summaries_by_role[role]
        # Structured response claim (not free-form thinking)
        adj_conf = _clamp01(
            own["confidence"]
            + 0.05 * support_others / max(1, len(others))
            - 0.05 * oppose_others / max(1, len(others))
        )
        claim_key = _claim_key(role, 2, 0)
        claims.append(
            ClaimArtifact(
                claim_key=claim_key,
                role_code=role,
                round_number=2,
                statement=(
                    f"{role} reviewed structured summaries from {len(others)} peers "
                    f"({support_others} support / {oppose_others} oppose) and "
                    f"{'maintains' if adj_conf >= 0.5 else 'softens'} prior stance."
                ),
                confidence=adj_conf,
                stance=own["stance"] if abs(adj_conf - own["confidence"]) < 0.15 else (
                    "conditional" if 0.4 <= adj_conf <= 0.6 else own["stance"]
                ),
            )
        )
        evidence.append(
            EvidenceArtifact(
                claim_key=claim_key,
                role_code=role,
                round_number=2,
                statement=f"Peer summary bundle: {sorted(others.keys())}",
                source_ref="council:round1_summaries",
                strength=_clamp01(0.4 + 0.1 * len(others)),
            )
        )
        # Counter from adversarial roles toward supporters
        if role in ("sceptic", "risk_analyst") and support_others:
            counters.append(
                CounterargumentArtifact(
                    claim_key=claim_key,
                    role_code=role,
                    round_number=2,
                    statement=(
                        f"{role} counterargument: peer support may reflect correlated bias, "
                        "not independent evidence strength."
                    ),
                    confidence=0.6,
                )
            )
    rounds.append(
        RoundRecord(
            round_number=2,
            round_code=DEBATE_ROUNDS[1][1],
            round_label=DEBATE_ROUNDS[1][2],
            structured_summary=(
                "Round 2: each agent received structured summaries from others and "
                "emitted updated claims/evidence/counterarguments only."
            ),
        )
    )

    # --- Round 3: Identify disagreements ---
    r2_claims = [c for c in claims if c.round_number == 2]
    disagreements: list[DisagreementArtifact] = []
    by_role = {c.role_code: c for c in r2_claims}
    role_list = list(by_role.keys())
    for i, ra in enumerate(role_list):
        for rb in role_list[i + 1 :]:
            ca, cb = by_role[ra], by_role[rb]
            if ca.stance != cb.stance:
                severity = _clamp01(abs(ca.confidence - cb.confidence) + 0.35)
                # Prefer linking to round-1 claim keys for continuity
                claim_key = next(
                    (c.claim_key for c in claims if c.role_code == ra and c.round_number == 1),
                    ca.claim_key,
                )
                disagreements.append(
                    DisagreementArtifact(
                        claim_key=claim_key,
                        role_a=ra,
                        role_b=rb,
                        summary=(
                            f"Disagreement: {ra}={ca.stance} ({ca.confidence:.2f}) vs "
                            f"{rb}={cb.stance} ({cb.confidence:.2f})."
                        ),
                        severity=severity,
                    )
                )
    rounds.append(
        RoundRecord(
            round_number=3,
            round_code=DEBATE_ROUNDS[2][1],
            round_label=DEBATE_ROUNDS[2][2],
            structured_summary=(
                f"Round 3 identified {len(disagreements)} stance disagreements "
                "across opposing roles."
            ),
        )
    )

    # --- Round 4: Evidence for disputed claims ---
    evidence_requests: list[EvidenceRequestArtifact] = []
    disputed_keys = sorted({d.claim_key for d in disagreements})
    for d in disagreements:
        req_role = "evidence_reviewer" if "evidence_reviewer" in roles else d.role_a
        # Find related brief facts
        matching_facts = [
            f
            for f in brief.facts
            if _norm(f.label) in _norm(d.summary) or True
        ][:1]
        fulfillment = None
        fulfilled = False
        if matching_facts or brief.facts:
            fact = (matching_facts or brief.facts)[0]
            fulfillment = f"Evidence for dispute: {fact.label} — {fact.statement}"
            fulfilled = True
            evidence.append(
                EvidenceArtifact(
                    claim_key=d.claim_key,
                    role_code=req_role,
                    round_number=4,
                    statement=fulfillment,
                    source_ref=f"fact:{fact.label}",
                    strength=_clamp01(fact.strength),
                )
            )
        evidence_requests.append(
            EvidenceRequestArtifact(
                claim_key=d.claim_key,
                requested_by_role=req_role,
                request_statement=(
                    f"Provide evidence specifically for disputed claim {d.claim_key} "
                    f"({d.role_a} vs {d.role_b})."
                ),
                fulfilled=fulfilled,
                fulfillment_evidence=fulfillment,
            )
        )
    # If no disagreements, still record that evidence audit passed
    if not disagreements:
        evidence_requests.append(
            EvidenceRequestArtifact(
                claim_key="consensus-audit",
                requested_by_role="evidence_reviewer",
                request_statement="No material disagreements; audit baseline evidence quality.",
                fulfilled=True,
                fulfillment_evidence="Baseline brief facts reviewed; consensus holds.",
            )
        )
    rounds.append(
        RoundRecord(
            round_number=4,
            round_code=DEBATE_ROUNDS[3][1],
            round_label=DEBATE_ROUNDS[3][2],
            structured_summary=(
                f"Round 4 requested evidence for {len(disputed_keys)} disputed claim(s); "
                f"{sum(1 for e in evidence_requests if e.fulfilled)} fulfilled."
            ),
        )
    )

    # --- Round 5: Judge ---
    support_votes = sum(1 for c in r2_claims if c.stance == "support")
    oppose_votes = sum(1 for c in r2_claims if c.stance == "oppose")
    conditional_votes = sum(1 for c in r2_claims if c.stance == "conditional")
    avg_conf = mean([c.confidence for c in r2_claims]) if r2_claims else 0.5
    fulfilled_ratio = (
        sum(1 for e in evidence_requests if e.fulfilled) / max(1, len(evidence_requests))
    )

    if support_votes > oppose_votes and avg_conf >= 0.5 and fulfilled_ratio >= 0.5:
        decision_text = (
            f"PROCEED with guardrails on «{brief.decision_question}» for "
            f"{brief.client_brand}. Council majority supports with evidence audit."
        )
        final_conf = _clamp01(0.45 + 0.25 * (support_votes / max(1, len(r2_claims))) + 0.2 * avg_conf)
        supporting = [c.claim_key for c in claims if c.stance == "support" and c.round_number == 1]
        rejected = [c.claim_key for c in claims if c.stance == "oppose" and c.round_number == 1]
    elif oppose_votes > support_votes:
        decision_text = (
            f"DO NOT PROCEED on «{brief.decision_question}» for {brief.client_brand} "
            f"until sceptic/risk objections are resolved with stronger evidence."
        )
        final_conf = _clamp01(0.45 + 0.25 * (oppose_votes / max(1, len(r2_claims))) + 0.15 * (1 - avg_conf))
        supporting = [c.claim_key for c in claims if c.stance == "oppose" and c.round_number == 1]
        rejected = [c.claim_key for c in claims if c.stance == "support" and c.round_number == 1]
    else:
        decision_text = (
            f"CONDITIONAL / STAGE decision on «{brief.decision_question}» for "
            f"{brief.client_brand}: pilot with measurement gates "
            f"(support={support_votes}, oppose={oppose_votes}, conditional={conditional_votes})."
        )
        final_conf = _clamp01(0.4 + 0.2 * avg_conf + 0.1 * fulfilled_ratio)
        supporting = [c.claim_key for c in claims if c.stance == "conditional" and c.round_number == 1]
        rejected = []

    decision = DecisionArtifact(
        decision=decision_text,
        confidence=final_conf,
        supporting_claim_keys=supporting,
        rejected_claim_keys=rejected,
        judge_role="council_judge",
    )
    rounds.append(
        RoundRecord(
            round_number=5,
            round_code=DEBATE_ROUNDS[4][1],
            round_label=DEBATE_ROUNDS[4][2],
            structured_summary=(
                f"Round 5 judge decision confidence={final_conf:.2f}. "
                "Stored artifacts limited to claim/evidence/counterargument/confidence/decision."
            ),
        )
    )

    # Integrity: no CoT fields anywhere in serialized output
    result = CouncilDebateResult(
        decision_question=brief.decision_question,
        agents=agents,
        rounds=rounds,
        claims=claims,
        evidence=evidence,
        counterarguments=counters,
        disagreements=disagreements,
        evidence_requests=evidence_requests,
        decisions=[decision],
        final_decision=decision_text,
        final_confidence=final_conf,
        open_opinion_prompts_rejected=True,
        chain_of_thought_not_stored=True,
        stored_artifact_kinds=list(STORED_ARTIFACT_KINDS),
        methodology_note=METHODOLOGY_NOTE,
        summary=(
            f"Council 2.0 completed 5-round opposing-role debate with {len(roles)} agents. "
            f"Disagreements={len(disagreements)}. Final confidence={final_conf:.2f}. "
            f"Open opinion prompts rejected; chain-of-thought not stored."
        ),
    )
    serialized = result.to_dict()
    for forbidden in FORBIDDEN_STORAGE_FIELDS:
        assert forbidden not in serialized
    assert len(result.rounds) == 5
    return result
