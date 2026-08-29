"""Strategic pipeline orchestrator — Layers 0–10 with Peacock mode budgets."""

from __future__ import annotations

from uuid import uuid4

from intelligence.context_selector import ContextSelector, default_demo_providers
from intelligence.layers import (
    layer0_classify,
    layer1_context,
    layer2_evidence,
    layer3_research,
    layer4_specialists,
    layer5_adversarial,
    layer6_verification,
    layer7_decision,
    layer8_simulation,
    layer9_execution,
    layer10_learning,
)
from intelligence.models import (
    LAYER_NAMES,
    LayerResult,
    PipelineResult,
    PipelineState,
    StrategicLayer,
    StrategicRequest,
)
from intelligence.peacock_modes import profile_for
from intelligence.research import MockResearchConnector


class StrategicPipeline:
    """Decomposes complex strategic requests into Layers 0–10 under a Peacock mode."""

    def __init__(
        self,
        *,
        context_selector: ContextSelector | None = None,
        research_connector: MockResearchConnector | None = None,
        llm_complete=None,
    ) -> None:
        self.context_selector = context_selector or ContextSelector(providers=default_demo_providers())
        self.research_connector = research_connector or MockResearchConnector()
        self.llm_complete = llm_complete

    async def run(self, request: StrategicRequest) -> PipelineResult:
        state = PipelineState(request=request)

        # Layer 0 always runs — selects Peacock mode + budget envelope
        state.layer_results.append(await layer0_classify(state))
        assert state.classification is not None
        skip = set(state.classification.skip_layers)
        mode_key = state.peacock_mode or state.classification.peacock_mode
        profile = profile_for(mode_key)
        caps = profile.capabilities

        async def maybe(layer: StrategicLayer, factory) -> None:
            tracker = state.mode_tracker
            if tracker is not None and not tracker.checkpoint():
                state.layer_results.append(
                    LayerResult(
                        layer=layer,
                        name=LAYER_NAMES[layer],
                        status="skipped",
                        summary=f"Skipped — mode budget exhausted ({tracker.usage.stopped_reason})",
                        output={
                            "skipped": True,
                            "reason": "mode_budget_exhausted",
                            "budget": tracker.snapshot(),
                        },
                    )
                )
                return

            # Mode capability gates (in addition to classification skip_layers)
            if layer == StrategicLayer.RESEARCH and not caps.enable_research:
                state.layer_results.append(
                    LayerResult(
                        layer=layer,
                        name=LAYER_NAMES[layer],
                        status="skipped",
                        summary=f"Skipped by {profile.display_name} (research disabled)",
                        output={"skipped": True, "reason": "mode_disables_research"},
                    )
                )
                return
            if layer == StrategicLayer.ADVERSARIAL_ANALYSIS and not (
                caps.enable_critic or caps.adversarial_reasoning
            ):
                state.layer_results.append(
                    LayerResult(
                        layer=layer,
                        name=LAYER_NAMES[layer],
                        status="skipped",
                        summary=f"Skipped by {profile.display_name} (critic disabled)",
                        output={"skipped": True, "reason": "mode_disables_critic"},
                    )
                )
                return
            if layer == StrategicLayer.VERIFICATION:
                # Standard: verification when required — skip if low risk and no blocks expected
                if caps.verification_when_required and not caps.enable_verification:
                    pass
                if not caps.enable_verification and not caps.verification_when_required:
                    state.layer_results.append(
                        LayerResult(
                            layer=layer,
                            name=LAYER_NAMES[layer],
                            status="skipped",
                            summary=f"Skipped by {profile.display_name} (verification disabled)",
                            output={"skipped": True, "reason": "mode_disables_verification"},
                        )
                    )
                    return
                if (
                    caps.verification_when_required
                    and state.classification
                    and state.classification.importance == "low"
                    and state.classification.business_risk == "low"
                    and not state.challenges
                ):
                    state.layer_results.append(
                        LayerResult(
                            layer=layer,
                            name=LAYER_NAMES[layer],
                            status="skipped",
                            summary="Verification not required (low risk, no challenges)",
                            output={"skipped": True, "reason": "verification_when_required"},
                        )
                    )
                    return

            if int(layer) in skip:
                state.layer_results.append(
                    LayerResult(
                        layer=layer,
                        name=LAYER_NAMES[layer],
                        status="skipped",
                        summary="Skipped by classification / mode policy",
                        output={"skipped": True, "reason": "classification.skip_layers"},
                    )
                )
                return

            if tracker is not None:
                tracker.record_call(cost_usd_micros=0)

            state.layer_results.append(await factory())

        await maybe(
            StrategicLayer.CONTEXT_ASSEMBLY,
            lambda: layer1_context(state, self.context_selector),
        )
        await maybe(StrategicLayer.DETERMINISTIC_EVIDENCE, lambda: layer2_evidence(state))
        await maybe(
            StrategicLayer.RESEARCH,
            lambda: layer3_research(state, self.research_connector),
        )
        await maybe(
            StrategicLayer.SPECIALIST_REASONING,
            lambda: layer4_specialists(state, self.llm_complete),
        )
        await maybe(StrategicLayer.ADVERSARIAL_ANALYSIS, lambda: layer5_adversarial(state))
        await maybe(StrategicLayer.VERIFICATION, lambda: layer6_verification(state))
        await maybe(StrategicLayer.DECISION, lambda: layer7_decision(state))
        await maybe(StrategicLayer.SIMULATION, lambda: layer8_simulation(state))
        await maybe(StrategicLayer.EXECUTION_PLAN, lambda: layer9_execution(state))
        await maybe(StrategicLayer.LEARNING, lambda: layer10_learning(state))

        failed = [layer for layer in state.layer_results if layer.status == "failed"]
        status = "failed" if failed else "completed"
        if state.verification and state.verification.blocked:
            status = "completed_with_blocks"
        if state.mode_tracker and state.mode_tracker.usage.stopped_reason:
            status = "completed_budget_limited"

        mode_payload = {
            **profile.to_dict(),
            "budget_usage": state.mode_tracker.snapshot() if state.mode_tracker else None,
            "lab_plan": state.lab_plan,
        }

        return PipelineResult(
            id=str(uuid4()),
            organisation_id=request.organisation_id,
            workspace_id=request.workspace_id,
            status=status,
            classification=state.classification,
            layers=state.layer_results,
            recommendations=state.recommendations,
            tasks=state.tasks,
            evidence_summary={
                "deterministic": len(state.evidence.deterministic),
                "research": len(state.evidence.research),
                "inferences": len(state.evidence.inferences),
            },
            context_summary={
                "selected_kinds": state.context.selected_kinds if state.context else [],
                "rejected_kinds": state.context.rejected_kinds if state.context else [],
                "tokens_used": state.context.tokens_used if state.context else 0,
                "token_budget": state.context.token_budget if state.context else 0,
                "item_count": len(state.context.items) if state.context else 0,
            },
            verification=state.verification,
            learning=state.learning,
            interpretation=(
                f"Ran under {profile.display_name}. "
                "Pipeline separates deterministic evidence from LLM inference. "
                "Recommendations are ranked with deterministic priority scores. "
                f"Budget envelope: max_cost={profile.budget.max_cost}, "
                f"max_calls={profile.budget.max_calls}, "
                f"max_iterations={profile.budget.max_iterations}, "
                f"max_runtime={profile.budget.max_runtime}."
            ),
            peacock_mode=mode_key,
            mode=mode_payload,
        )
