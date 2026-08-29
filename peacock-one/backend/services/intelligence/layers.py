"""Layer implementations for the strategic intelligence pipeline."""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Awaitable

from scoring import weighted_score
from intelligence.context_selector import CONTEXT_CATALOG, ContextSelector, default_demo_providers
from intelligence.evidence import collect_deterministic_evidence
from intelligence.models import (
    Challenge,
    EvidenceItem,
    EvidenceKind,
    ExecutionTask,
    LAYER_NAMES,
    LayerResult,
    LearningRecord,
    PipelineState,
    RankedRecommendation,
    RequestClassification,
    SimulationOutcome,
    SpecialistOutput,
    StrategicLayer,
    ThinkingDepth,
    VerificationResult,
)
from intelligence.research import MockResearchConnector

LayerFn = Callable[[PipelineState], Awaitable[LayerResult]]


def _ms_since(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _keyword_intent(text: str) -> tuple[str, str, list[str]]:
    lower = text.lower()
    if any(k in lower for k in ("seo audit", "technical seo", "crawl issue", "indexability")):
        return (
            "seo_audit_review",
            "ranked_seo_recommendations",
            ["seo_audit_summary", "crawl_summary", "website_architecture"],
        )
    if any(k in lower for k in ("content strategy", "editorial", "blog", "topic cluster")):
        return (
            "content_strategy",
            "content_roadmap",
            ["existing_content", "audience", "personas", "writer_pool", "competitors"],
        )
    if any(k in lower for k in ("competitor", "competitive", "share of voice")):
        return (
            "competitive_analysis",
            "competitive_brief",
            ["competitors", "brand", "historical_performance"],
        )
    if any(k in lower for k in ("fix broken", "orphan", "redirect", "canonical")):
        return (
            "technical_fix",
            "technical_fix_plan",
            ["crawl_summary", "website_architecture", "seo_audit_summary"],
        )
    if any(k in lower for k in ("visibility", "aeo", "geo", "citation", "brand mention")):
        return (
            "visibility_growth",
            "visibility_strategy",
            ["brand", "competitors", "historical_performance", "existing_content"],
        )
    if any(k in lower for k in ("execute", "roadmap", "sprint", "implementation")):
        return (
            "execution_planning",
            "execution_plan",
            ["previous_recommendations", "writer_pool", "conversion_objectives"],
        )
    return (
        "general_strategy",
        "strategic_recommendations",
        ["brand", "business_model", "audience", "conversion_objectives", "competitors"],
    )


async def layer0_classify(state: PipelineState) -> LayerResult:
    start = time.perf_counter()
    from intelligence.peacock_modes import (
        LabExperimentPlan,
        ModeBudgetTracker,
        profile_for,
        resolve_mode,
    )

    text = state.request.request_text
    intent, default_output, required = _keyword_intent(text)
    requested_output = state.request.requested_output or default_output

    importance_val = "medium"
    risk_val = "medium"
    freshness = "recent"
    depth = ThinkingDepth.STANDARD
    skip: list[int] = []

    lower = text.lower()
    if any(k in lower for k in ("urgent", "critical", "revenue", "legal", "brand risk")):
        importance_val = "critical"
        risk_val = "high"
        depth = ThinkingDepth.COUNCIL
    elif any(k in lower for k in ("lab", "experiment", "hypothesis", "a/b", "prompt experiment")):
        importance_val = "medium"
        risk_val = "low"
        depth = ThinkingDepth.LAB
    elif any(k in lower for k in ("quick", "summary", "status", "fast")):
        importance_val = "low"
        risk_val = "low"
        depth = ThinkingDepth.SHALLOW
    elif any(k in lower for k in ("deep dive", "board", "quarterly", "strategy", "multi-agent")):
        importance_val = "high"
        risk_val = "medium"
        depth = ThinkingDepth.DEEP

    if any(k in lower for k in ("live", "today", "breaking", "fresh")):
        freshness = "realtime"
    elif any(k in lower for k in ("historical", "trend", "over time")):
        freshness = "stale_ok"

    # Resolve Peacock mode (explicit request wins)
    explicit_mode = state.request.peacock_mode or (state.request.metadata or {}).get("peacock_mode")
    mode = resolve_mode(explicit=explicit_mode, thinking_depth=depth, request_text=text)
    profile = profile_for(mode)
    depth = profile.thinking_depth
    skip = list(profile.skip_layers)

    # Standard: verification when required — skip adversarial for low-risk simple asks
    if (
        mode.value == "peacock_standard"
        and importance_val == "low"
        and risk_val == "low"
        and int(StrategicLayer.ADVERSARIAL_ANALYSIS) not in skip
    ):
        skip = [*skip, int(StrategicLayer.ADVERSARIAL_ANALYSIS)]

    lab_plan = None
    if mode.value == "peacock_lab":
        plan = LabExperimentPlan(
            repeated_measurements=any(k in lower for k in ("repeat", "measurement", "n=")),
            prompt_experiments=any(k in lower for k in ("prompt", "wording")),
            content_simulations=any(k in lower for k in ("simulation", "simulate")),
            controlled_comparisons=any(k in lower for k in ("compare", "a/b", "control")),
            hypothesis_tests=any(k in lower for k in ("hypothesis", "test whether")),
            measurement_rounds=3 if "repeat" in lower else 1,
        )
        # Default Lab enables the full experimental toolkit when unspecified
        if not any(
            [
                plan.repeated_measurements,
                plan.prompt_experiments,
                plan.content_simulations,
                plan.controlled_comparisons,
                plan.hypothesis_tests,
            ]
        ):
            plan = LabExperimentPlan(
                repeated_measurements=True,
                prompt_experiments=True,
                content_simulations=True,
                controlled_comparisons=True,
                hypothesis_tests=True,
                measurement_rounds=3,
            )
        lab_plan = plan.to_dict()

    # Expand required_data to valid catalogue keys only
    required_data = [k for k in required if k in CONTEXT_CATALOG]

    classification = RequestClassification(
        user_intent=intent,
        requested_output=requested_output,
        importance=importance_val,  # type: ignore[arg-type]
        business_risk=risk_val,  # type: ignore[arg-type]
        freshness_requirement=freshness,  # type: ignore[arg-type]
        required_data=required_data,
        thinking_depth=depth,
        peacock_mode=mode.value,
        mode_budget=profile.budget.to_dict(),
        mode_capabilities=profile.capabilities.to_dict(),
        intent_confidence=0.82,
        skip_layers=skip,
        notes=(
            f"{profile.display_name}: {profile.summary} "
            f"(max_cost={profile.budget.max_cost}, max_calls={profile.budget.max_calls}, "
            f"max_iterations={profile.budget.max_iterations}, max_runtime={profile.budget.max_runtime})."
        ),
    )
    state.classification = classification
    state.peacock_mode = mode.value
    state.mode_tracker = ModeBudgetTracker(profile.budget)
    # Layer 0 counts as one call toward the mode envelope
    state.mode_tracker.record_call(cost_usd_micros=0)
    state.lab_plan = lab_plan

    return LayerResult(
        layer=StrategicLayer.REQUEST_CLASSIFICATION,
        name=LAYER_NAMES[StrategicLayer.REQUEST_CLASSIFICATION],
        status="completed",
        summary=f"Intent={intent}, mode={mode.value}, depth={depth.value}, risk={risk_val}",
        duration_ms=_ms_since(start),
        output={
            **classification.to_dict(),
            "mode_profile": profile.to_dict(),
            "lab_plan": lab_plan,
        },
    )


async def layer1_context(state: PipelineState, selector: ContextSelector | None = None) -> LayerResult:
    start = time.perf_counter()
    assert state.classification is not None
    selector = selector or ContextSelector(providers=default_demo_providers())
    # Inject crawl/seo summaries from request metadata as high-signal context
    meta = state.request.metadata or {}
    extra_providers = list(selector.providers)
    from intelligence.context_selector import InMemoryContextProvider
    from intelligence.models import ContextItem

    if meta.get("crawl") or state.request.crawl_id:
        crawl = meta.get("crawl") or {}
        extra_providers.append(
            InMemoryContextProvider(
                "crawl_summary",
                [
                    ContextItem(
                        "crawl_summary",
                        "crawl.latest",
                        f"Crawl {state.request.crawl_id or 'inline'}: "
                        f"{crawl.get('pages_crawled', '?')} pages, "
                        f"{crawl.get('issues_found', '?')} issues",
                        0.95,
                        45,
                        "request_metadata",
                        payload=crawl,
                    )
                ],
            )
        )
    if meta.get("seo_audit") or state.request.audit_id:
        audit = meta.get("seo_audit") or {}
        extra_providers.append(
            InMemoryContextProvider(
                "seo_audit_summary",
                [
                    ContextItem(
                        "seo_audit_summary",
                        "seo.latest",
                        f"Peacock SEO Score {audit.get('peacock_seo_score', 'n/a')}",
                        0.95,
                        40,
                        "request_metadata",
                        payload=audit,
                    )
                ],
            )
        )
    selector = ContextSelector(
        providers=extra_providers,
        token_budget=selector.token_budget,
        max_items=selector.max_items,
    )
    bundle = selector.assemble(state.request, state.classification)
    state.context = bundle
    return LayerResult(
        layer=StrategicLayer.CONTEXT_ASSEMBLY,
        name=LAYER_NAMES[StrategicLayer.CONTEXT_ASSEMBLY],
        status="completed",
        summary=f"Selected {len(bundle.items)} fragments ({bundle.tokens_used}/{bundle.token_budget} tokens)",
        duration_ms=_ms_since(start),
        output=bundle.to_dict(),
    )


async def layer2_evidence(state: PipelineState) -> LayerResult:
    start = time.perf_counter()
    bundle = collect_deterministic_evidence(state)
    # Preserve any research already present
    bundle.research = list(state.evidence.research)
    bundle.inferences = list(state.evidence.inferences)
    state.evidence = bundle
    return LayerResult(
        layer=StrategicLayer.DETERMINISTIC_EVIDENCE,
        name=LAYER_NAMES[StrategicLayer.DETERMINISTIC_EVIDENCE],
        status="completed",
        summary=f"Collected {len(bundle.deterministic)} deterministic evidence items",
        duration_ms=_ms_since(start),
        output={
            "deterministic_count": len(bundle.deterministic),
            "items": [e.to_dict() for e in bundle.deterministic[:50]],
            "separation": "Deterministic evidence isolated from LLM inference",
        },
    )


async def layer3_research(
    state: PipelineState,
    connector: MockResearchConnector | None = None,
) -> LayerResult:
    start = time.perf_counter()
    assert state.classification is not None
    if state.classification.freshness_requirement == "stale_ok":
        return LayerResult(
            layer=StrategicLayer.RESEARCH,
            name=LAYER_NAMES[StrategicLayer.RESEARCH],
            status="skipped",
            summary="Freshness requirement allows stale evidence — research skipped",
            duration_ms=_ms_since(start),
            output={"skipped": True},
        )
    connector = connector or MockResearchConnector()
    query = state.request.request_text
    items = await connector.research(query, organisation_id=state.request.organisation_id)
    state.evidence.research.extend(items)
    return LayerResult(
        layer=StrategicLayer.RESEARCH,
        name=LAYER_NAMES[StrategicLayer.RESEARCH],
        status="completed",
        summary=f"Collected {len(items)} research evidence item(s) via {connector.name}",
        duration_ms=_ms_since(start),
        output={"items": [i.to_dict() for i in items], "connector": connector.name},
    )


async def layer4_specialists(state: PipelineState, llm_complete: Any | None = None) -> LayerResult:
    start = time.perf_counter()
    assert state.classification is not None
    specialists: list[SpecialistOutput] = []

    # Deterministic specialist: evidence synthesizer (not LLM)
    det_codes = [e.code for e in state.evidence.deterministic]
    det_summary = (
        f"Deterministic specialist reviewed {len(det_codes)} quantitative signals "
        f"for intent={state.classification.user_intent}."
    )
    claims = []
    for item in state.evidence.deterministic[:8]:
        claims.append(f"{item.label}={item.value}")
    specialists.append(
        SpecialistOutput(
            agent_name="deterministic_analyst",
            role="SYNTHESIS",
            summary=det_summary,
            claims=claims,
            confidence=0.9,
            evidence_refs=det_codes[:12],
            is_llm_derived=False,
        )
    )

    # LLM specialist via optional callback / null-friendly structured output
    llm_summary = "Specialist reasoning deferred to structured heuristic synthesis."
    if llm_complete is not None:
        try:
            llm_summary = await llm_complete(state)
        except Exception as exc:  # noqa: BLE001
            llm_summary = f"LLM specialist unavailable ({exc}); used heuristic synthesis."

    # Heuristic specialist claims derived from evidence (explicitly tagged as inference aids)
    inference_claims = []
    score = next((e for e in state.evidence.deterministic if e.code == "seo.peacock_score"), None)
    if score and float(score.value) < 70:
        inference_claims.append("SEO score below 70 suggests prioritising technical and content fixes.")
    issues = next((e for e in state.evidence.deterministic if e.code == "seo.critical_issues"), None)
    if issues and int(issues.value) > 0:
        inference_claims.append("Critical SEO issues should precede growth experiments.")
    if not inference_claims:
        inference_claims.append("No critical quantitative red flags; pursue balanced growth recommendations.")

    specialists.append(
        SpecialistOutput(
            agent_name="strategy_specialist",
            role="SYNTHESIS",
            summary=llm_summary if isinstance(llm_summary, str) else str(llm_summary),
            claims=inference_claims,
            confidence=0.65,
            evidence_refs=det_codes[:8],
            is_llm_derived=True,
        )
    )
    # Record inferences separately from deterministic evidence
    for claim in inference_claims:
        state.evidence.inferences.append(
            EvidenceItem(
                code=f"inference.{abs(hash(claim)) % 10_000}",
                label="Specialist inference",
                value=claim,
                kind=EvidenceKind.LLM_INFERENCE,
                source="strategy_specialist",
                confidence=0.65,
            )
        )

    state.specialists = specialists
    return LayerResult(
        layer=StrategicLayer.SPECIALIST_REASONING,
        name=LAYER_NAMES[StrategicLayer.SPECIALIST_REASONING],
        status="completed",
        summary=f"Ran {len(specialists)} specialists",
        duration_ms=_ms_since(start),
        output={"specialists": [s.to_dict() for s in specialists]},
    )


async def layer5_adversarial(state: PipelineState) -> LayerResult:
    start = time.perf_counter()
    challenges: list[Challenge] = []
    for specialist in state.specialists:
        for claim in specialist.claims:
            severity = "medium"
            challenge = "Is this claim supported by deterministic evidence?"
            supported = any(
                str(item.value).lower() in claim.lower() or item.label.lower() in claim.lower()
                for item in state.evidence.deterministic
            )
            if specialist.is_llm_derived and not supported:
                severity = "high"
                challenge = "LLM-derived claim lacks direct deterministic evidence support."
            elif "priorit" in claim.lower() and state.classification and state.classification.business_risk == "low":
                severity = "low"
                challenge = "Priority may be overstated relative to business risk."
            challenges.append(
                Challenge(
                    claim=claim,
                    challenge=challenge,
                    severity=severity,  # type: ignore[arg-type]
                    unresolved=not supported and specialist.is_llm_derived,
                )
            )
    if not challenges:
        challenges.append(
            Challenge(
                claim="(none)",
                challenge="No specialist claims to challenge.",
                severity="low",
                unresolved=False,
            )
        )
    state.challenges = challenges
    return LayerResult(
        layer=StrategicLayer.ADVERSARIAL_ANALYSIS,
        name=LAYER_NAMES[StrategicLayer.ADVERSARIAL_ANALYSIS],
        status="completed",
        summary=f"{sum(1 for c in challenges if c.unresolved)} unresolved challenges",
        duration_ms=_ms_since(start),
        output={"challenges": [c.to_dict() for c in challenges]},
    )


async def layer6_verification(state: PipelineState) -> LayerResult:
    start = time.perf_counter()
    checks: list[str] = []
    failures: list[str] = []

    checks.append("Deterministic evidence bundle present")
    if not state.evidence.deterministic and not state.evidence.research:
        failures.append("No deterministic or research evidence collected")

    checks.append("Context selection respected token budget")
    if state.context and state.context.tokens_used > state.context.token_budget:
        failures.append("Context exceeded token budget")

    checks.append("Inferences tagged separately from deterministic evidence")
    leaked = [e for e in state.evidence.deterministic if e.kind != EvidenceKind.DETERMINISTIC]
    if leaked:
        failures.append("Non-deterministic items leaked into deterministic evidence")

    unresolved_high = [c for c in state.challenges if c.unresolved and c.severity == "high"]
    checks.append("High-severity adversarial challenges reviewed")
    blocked = False
    if unresolved_high and state.classification and state.classification.business_risk in {"high", "critical"}:
        blocked = True
        failures.append("High-severity unresolved challenges under elevated business risk")

    consensus = 1.0
    if state.challenges:
        resolved = sum(1 for c in state.challenges if not c.unresolved)
        consensus = resolved / max(len(state.challenges), 1)
    if failures:
        consensus = min(consensus, 0.55)

    verification = VerificationResult(
        consistent=not failures,
        blocked=blocked,
        consensus_score=round(consensus, 4),
        checks=checks,
        failures=failures,
    )
    state.verification = verification
    return LayerResult(
        layer=StrategicLayer.VERIFICATION,
        name=LAYER_NAMES[StrategicLayer.VERIFICATION],
        status="completed",
        summary=f"consistent={verification.consistent}, blocked={blocked}, consensus={consensus}",
        duration_ms=_ms_since(start),
        output=verification.to_dict(),
    )


async def layer7_decision(state: PipelineState) -> LayerResult:
    start = time.perf_counter()
    recs: list[RankedRecommendation] = []

    def add(title: str, rationale: str, *, impact: float, effort: float, confidence: float, refs: list[str], inference: bool = False, priority: str | None = None) -> None:
        score = weighted_score(impact, confidence, effort)
        if priority is None:
            if score >= 0.7:
                priority = "critical" if impact >= 0.85 else "high"
            elif score >= 0.45:
                priority = "medium"
            else:
                priority = "low"
        recs.append(
            RankedRecommendation(
                title=title,
                rationale=rationale,
                priority=priority,  # type: ignore[arg-type]
                impact=impact,
                effort=effort,
                confidence=confidence,
                priority_score=round(score, 4),
                evidence_refs=refs,
                depends_on_inference=inference,
            )
        )

    # Deterministic recommendation generation from evidence
    for item in state.evidence.deterministic:
        if item.code.startswith("seo.critical") or (item.code.endswith("critical_issues") and int(item.value) > 0):
            add(
                "Resolve critical SEO issues first",
                f"Deterministic signal {item.code}={item.value}.",
                impact=0.95,
                effort=0.55,
                confidence=0.92,
                refs=[item.code],
            )
        if item.code == "crawl.pages_failed" and int(item.value) > 0:
            add(
                "Repair failed crawl URLs",
                f"{item.value} pages failed during crawl.",
                impact=0.8,
                effort=0.4,
                confidence=0.9,
                refs=[item.code],
            )
        if item.code == "seo.peacock_score" and float(item.value) < 70:
            add(
                "Raise Peacock SEO Score above 70",
                f"Current score {item.value} is below target threshold.",
                impact=0.85,
                effort=0.65,
                confidence=0.88,
                refs=[item.code],
            )
        if item.code == "vis.brand_mentions" and float(item.value) < 5:
            add(
                "Increase brand mention visibility in AI answers",
                f"Brand mentions are low ({item.value}).",
                impact=0.7,
                effort=0.6,
                confidence=0.7,
                refs=[item.code],
            )

    # Specialist inference-backed recommendations (explicitly flagged)
    for specialist in state.specialists:
        if not specialist.is_llm_derived:
            continue
        for claim in specialist.claims[:2]:
            add(
                re.sub(r"\.$", "", claim)[:120],
                f"Derived from specialist {specialist.agent_name}; verify against deterministic evidence.",
                impact=0.55,
                effort=0.5,
                confidence=min(0.7, specialist.confidence),
                refs=specialist.evidence_refs[:5],
                inference=True,
                priority="medium",
            )

    if not recs:
        add(
            "Establish baseline measurement instrumentation",
            "Insufficient quantitative signals for aggressive changes.",
            impact=0.5,
            effort=0.35,
            confidence=0.75,
            refs=[],
        )

    if state.verification and state.verification.blocked:
        # Downgrade inference-heavy recs when blocked
        for rec in recs:
            if rec.depends_on_inference:
                rec.priority = "low"
                rec.confidence = min(rec.confidence, 0.4)
                rec.priority_score = weighted_score(rec.impact, rec.confidence, rec.effort)

    recs.sort(key=lambda r: (-r.priority_score, r.title))
    state.recommendations = recs
    return LayerResult(
        layer=StrategicLayer.DECISION,
        name=LAYER_NAMES[StrategicLayer.DECISION],
        status="completed",
        summary=f"Generated {len(recs)} ranked recommendations",
        duration_ms=_ms_since(start),
        output={"recommendations": [r.to_dict() for r in recs]},
    )


async def layer8_simulation(state: PipelineState) -> LayerResult:
    start = time.perf_counter()
    sims: list[SimulationOutcome] = []
    for rec in state.recommendations[:5]:
        upside = f"If successful, expect progress on '{rec.title}' with impact≈{rec.impact}."
        downside = "Opportunity cost and implementation risk if effort is underestimated."
        alternatives = [
            f"Defer '{rec.title}' and monitor for 2 weeks",
            f"Run a smaller pilot for '{rec.title}'",
        ]
        sims.append(
            SimulationOutcome(
                recommendation_title=rec.title,
                expected_upside=upside,
                expected_downside=downside,
                alternatives=alternatives,
                confidence=min(0.75, rec.confidence),
            )
        )
    state.simulations = sims
    return LayerResult(
        layer=StrategicLayer.SIMULATION,
        name=LAYER_NAMES[StrategicLayer.SIMULATION],
        status="completed",
        summary=f"Simulated {len(sims)} recommendation outcomes",
        duration_ms=_ms_since(start),
        output={"simulations": [s.to_dict() for s in sims]},
    )


async def layer9_execution(state: PipelineState) -> LayerResult:
    start = time.perf_counter()
    tasks: list[ExecutionTask] = []
    for index, rec in enumerate(state.recommendations[:8]):
        owner = "seo_engineer" if "seo" in rec.title.lower() or "crawl" in rec.title.lower() else "content_strategist"
        if "writer" in rec.title.lower() or "content" in rec.title.lower():
            owner = "editor"
        tasks.append(
            ExecutionTask(
                title=f"Execute: {rec.title}",
                description=rec.rationale,
                owner_role=owner,
                priority=rec.priority,
                depends_on=[] if index == 0 else [tasks[index - 1].title],
                success_metric=f"Move related evidence refs {', '.join(rec.evidence_refs[:3]) or 'baseline'} positively",
            )
        )
    state.tasks = tasks
    return LayerResult(
        layer=StrategicLayer.EXECUTION_PLAN,
        name=LAYER_NAMES[StrategicLayer.EXECUTION_PLAN],
        status="completed",
        summary=f"Created {len(tasks)} execution tasks",
        duration_ms=_ms_since(start),
        output={"tasks": [t.to_dict() for t in tasks]},
    )


async def layer10_learning(state: PipelineState) -> LayerResult:
    start = time.perf_counter()
    records: list[LearningRecord] = []
    for rec in state.recommendations[:8]:
        records.append(
            LearningRecord(
                recommendation_title=rec.title,
                expected_metric=rec.evidence_refs[0] if rec.evidence_refs else "manual_kpi",
                baseline_note="Record baseline before execution for outcome learning.",
                feature_hints=[
                    f"intent:{state.classification.user_intent if state.classification else 'unknown'}",
                    f"priority_score:{rec.priority_score}",
                    f"inference:{rec.depends_on_inference}",
                ],
            )
        )
    state.learning = records
    return LayerResult(
        layer=StrategicLayer.LEARNING,
        name=LAYER_NAMES[StrategicLayer.LEARNING],
        status="completed",
        summary=f"Recorded {len(records)} learning hooks for future weight updates",
        duration_ms=_ms_since(start),
        output={"learning": [r.to_dict() for r in records]},
    )
