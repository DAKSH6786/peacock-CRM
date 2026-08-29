"""Measurement Agent — summarises real before/after snapshot comparisons."""

from __future__ import annotations

from measurement.models import MeasurementComparison

from peacock_agents.models import AgentResult


def run_measurement_agent(comparison: MeasurementComparison) -> AgentResult:
    findings = [f"{d.metric}: {d.baseline} -> {d.latest} ({d.absolute_delta:+g})" for d in comparison.deltas if d.absolute_delta is not None]
    return AgentResult(
        agent_name="Measurement Agent",
        summary=f"Comparison period: {comparison.period_label}. {comparison.note}",
        findings=findings or ["Not enough snapshot history yet for this page."],
        recommendations=[
            f"{k.replace('_', ' ')}: {v}" for k, v in comparison.external_metrics.items()
        ],
    )
