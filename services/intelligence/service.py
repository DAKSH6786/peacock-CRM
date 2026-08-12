"""Intelligence orchestrator facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from intelligence.models import PipelineResult, StrategicRequest
from intelligence.pipeline import StrategicPipeline


@dataclass
class IntelligenceOrchestrator:
    """Organisation-scoped entrypoint for Layers 0–10 strategic decomposition."""

    organisation_id: str
    pipeline: StrategicPipeline = field(default_factory=StrategicPipeline)
    _runs: dict[str, PipelineResult] = field(default_factory=dict)

    def status(self) -> dict[str, Any]:
        from intelligence.peacock_modes import list_mode_catalog

        return {
            "service": "intelligence",
            "name": "Peacock Strategic Intelligence",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": True,
            "layers": [
                "0_request_classification",
                "1_context_assembly",
                "2_deterministic_evidence",
                "3_research",
                "4_specialist_reasoning",
                "5_adversarial_analysis",
                "6_verification",
                "7_decision",
                "8_simulation",
                "9_execution_plan",
                "10_learning",
            ],
            "peacock_modes": list_mode_catalog(),
            "guarantees": [
                "intelligent_context_selection",
                "no_full_database_dump",
                "deterministic_evidence_separated_from_llm_inference",
                "mode_budget_envelopes",
            ],
        }

    async def run_strategy(self, request: StrategicRequest) -> PipelineResult:
        if request.organisation_id != self.organisation_id:
            raise PermissionError("Organisation mismatch")
        result = await self.pipeline.run(request)
        self._runs[result.id] = result
        return result

    def get_run(self, run_id: str) -> PipelineResult | None:
        return self._runs.get(run_id)
