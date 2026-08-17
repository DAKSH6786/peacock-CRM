"""Enterprise Reliability service — persist resilient multi-provider runs."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.enterprise_reliability import (
    METHODOLOGY,
    PARTIAL_RESULTS_POLICY,
    RELIABILITY_POSITIONING,
    EnterpriseReliabilityRun,
    ErCircuitState,
    ErControlActivation,
    ErDeadLetterEvent,
    ErProviderMeasurement,
    ErWorkflowCheckpoint,
)
from enterprise_reliability.engine import (
    CircuitStateResult,
    ControlActivationResult,
    DeadLetterResult,
    ProviderMeasurementResult,
    ReliabilityRunResult,
    WorkflowCheckpointResult,
    analyse_reliability_run,
)
from enterprise_reliability.models import (
    EnterpriseReliabilityCreateSpec,
    EnterpriseReliabilityReport,
)


class EnterpriseReliabilityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: EnterpriseReliabilityCreateSpec,
        created_by: str | None = None,
    ) -> EnterpriseReliabilityReport:
        result = analyse_reliability_run(spec.run)

        row = EnterpriseReliabilityRun(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            report_status=result.report_status,
            engines_attempted=result.engines_attempted,
            engines_succeeded=result.engines_succeeded,
            engines_failed=result.engines_failed,
            partial_result_summary=result.partial_result_summary,
            unavailable_providers=",".join(result.unavailable_providers),
            idempotency_key=result.idempotency_key,
            cancelled=result.cancelled,
            recovered_from_checkpoint=result.recovered_from_checkpoint,
            cost_limit_usd_micros=result.cost_limit_usd_micros,
            cost_used_usd_micros=result.cost_used_usd_micros,
            rate_limit_rpm=result.rate_limit_rpm,
            dlq_events_count=result.dlq_events_count,
            controls_active_count=result.controls_active_count,
            methodology=METHODOLOGY,
            reliability_positioning=RELIABILITY_POSITIONING,
            partial_results_policy=PARTIAL_RESULTS_POLICY,
            summary=result.summary,
            analysed_at=result.analysed_at,
            notes=spec.notes,
        )
        self.db.add(row)
        self.db.flush()

        for p in result.provider_measurements:
            self.db.add(
                ErProviderMeasurement(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    run_id=row.id,
                    engine_code=p.engine_code,
                    engine_name=p.engine_name,
                    provider_code=p.provider_code,
                    outcome=p.outcome,
                    attempts=p.attempts,
                    failover_from=p.failover_from,
                    latency_ms=p.latency_ms,
                    cost_usd_micros=p.cost_usd_micros,
                    error_message=p.error_message,
                    included_in_report=p.included_in_report,
                    rank_order=p.rank_order,
                )
            )
        for c in result.control_activations:
            self.db.add(
                ErControlActivation(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    run_id=row.id,
                    control_kind=c.control_kind,
                    control_label=c.control_label,
                    active=c.active,
                    detail=c.detail,
                    rank_order=c.rank_order,
                )
            )
        for d in result.dead_letter_events:
            self.db.add(
                ErDeadLetterEvent(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    run_id=row.id,
                    source_kind=d.source_kind,
                    source_ref=d.source_ref,
                    error_class=d.error_class,
                    error_message=d.error_message,
                    attempts=d.attempts,
                    replay_status=d.replay_status,
                    payload_summary=d.payload_summary,
                )
            )
        for c in result.circuit_states:
            self.db.add(
                ErCircuitState(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    run_id=row.id,
                    provider_code=c.provider_code,
                    circuit_state=c.circuit_state,
                    failure_count=c.failure_count,
                    cooldown_seconds=c.cooldown_seconds,
                    reason=c.reason,
                )
            )
        for w in result.workflow_checkpoints:
            self.db.add(
                ErWorkflowCheckpoint(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    run_id=row.id,
                    phase=w.phase,
                    checkpoint_status=w.checkpoint_status,
                    detail=w.detail,
                    resumable=w.resumable,
                    rank_order=w.rank_order,
                )
            )

        self.db.commit()
        return EnterpriseReliabilityReport(
            run_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )

    def get_run(
        self, *, run_id: str, organisation_id: str
    ) -> EnterpriseReliabilityReport | None:
        row = self.db.scalar(
            select(EnterpriseReliabilityRun).where(
                EnterpriseReliabilityRun.id == run_id,
                EnterpriseReliabilityRun.organisation_id == organisation_id,
            )
        )
        if row is None:
            return None

        measurements = [
            ProviderMeasurementResult(
                engine_code=p.engine_code,
                engine_name=p.engine_name,
                provider_code=p.provider_code,
                outcome=p.outcome,
                attempts=p.attempts,
                failover_from=p.failover_from,
                latency_ms=p.latency_ms,
                cost_usd_micros=p.cost_usd_micros,
                error_message=p.error_message,
                included_in_report=p.included_in_report,
                rank_order=p.rank_order,
            )
            for p in self.db.scalars(
                select(ErProviderMeasurement)
                .where(ErProviderMeasurement.run_id == row.id)
                .order_by(ErProviderMeasurement.rank_order.asc())
            ).all()
        ]
        controls = [
            ControlActivationResult(
                control_kind=c.control_kind,
                control_label=c.control_label,
                active=c.active,
                detail=c.detail,
                rank_order=c.rank_order,
            )
            for c in self.db.scalars(
                select(ErControlActivation)
                .where(ErControlActivation.run_id == row.id)
                .order_by(ErControlActivation.rank_order.asc())
            ).all()
        ]
        dlq = [
            DeadLetterResult(
                source_kind=d.source_kind,
                source_ref=d.source_ref,
                error_class=d.error_class,
                error_message=d.error_message,
                attempts=d.attempts,
                replay_status=d.replay_status,
                payload_summary=d.payload_summary,
            )
            for d in self.db.scalars(
                select(ErDeadLetterEvent).where(ErDeadLetterEvent.run_id == row.id)
            ).all()
        ]
        circuits = [
            CircuitStateResult(
                provider_code=c.provider_code,
                circuit_state=c.circuit_state,
                failure_count=c.failure_count,
                cooldown_seconds=c.cooldown_seconds,
                reason=c.reason,
            )
            for c in self.db.scalars(
                select(ErCircuitState).where(ErCircuitState.run_id == row.id)
            ).all()
        ]
        checkpoints = [
            WorkflowCheckpointResult(
                phase=w.phase,
                checkpoint_status=w.checkpoint_status,
                detail=w.detail,
                resumable=w.resumable,
                rank_order=w.rank_order,
            )
            for w in self.db.scalars(
                select(ErWorkflowCheckpoint)
                .where(ErWorkflowCheckpoint.run_id == row.id)
                .order_by(ErWorkflowCheckpoint.rank_order.asc())
            ).all()
        ]

        from db_models.enterprise_reliability import METHODOLOGY_NOTE

        unavailable = [
            p for p in (row.unavailable_providers or "").split(",") if p.strip()
        ]
        result = ReliabilityRunResult(
            client_brand=row.client_brand,
            report_status=row.report_status,
            engines_attempted=row.engines_attempted,
            engines_succeeded=row.engines_succeeded,
            engines_failed=row.engines_failed,
            partial_result_summary=row.partial_result_summary,
            unavailable_providers=unavailable,
            idempotency_key=row.idempotency_key,
            cancelled=row.cancelled,
            recovered_from_checkpoint=row.recovered_from_checkpoint,
            cost_limit_usd_micros=row.cost_limit_usd_micros,
            cost_used_usd_micros=row.cost_used_usd_micros,
            rate_limit_rpm=row.rate_limit_rpm,
            dlq_events_count=row.dlq_events_count,
            controls_active_count=row.controls_active_count,
            provider_measurements=measurements,
            control_activations=controls,
            dead_letter_events=dlq,
            circuit_states=circuits,
            workflow_checkpoints=checkpoints,
            reliability_positioning=row.reliability_positioning,
            partial_results_policy=row.partial_results_policy,
            methodology_note=METHODOLOGY_NOTE,
            summary=row.summary,
            analysed_at=row.analysed_at,
        )
        return EnterpriseReliabilityReport(
            run_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )
