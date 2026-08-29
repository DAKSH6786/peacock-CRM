"""Monitoring engine — metric snapshots, history, jobs, learning hooks."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.monitoring import MetricSnapshot, MonitoringProject, SearchPerformanceSnapshot


@dataclass(slots=True)
class MonitoringEngine:
    organisation_id: str

    def status(self) -> dict[str, Any]:
        return {
            "service": "monitoring_engine",
            "organisation_id": self.organisation_id,
            "ready": True,
            "features_implemented": True,
            "persists_to": ["monitoring_projects", "metric_snapshots", "search_performance_snapshots"],
            "job": "peacock.monitoring.snapshot",
            "honesty": (
                "Monitoring stores real metric and search-performance snapshots. "
                "Scheduled updates use the job runner (memory/celery). "
                "Material deltas can emit learning_engine2 records and anomaly observations."
            ),
        }


class MonitoringService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_project(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        website_id: str,
        name: str,
        cadence: str = "weekly",
        created_by: str | None = None,
    ) -> MonitoringProject:
        project = MonitoringProject(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=website_id,
            name=name,
            cadence=cadence,
            is_active=True,
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, *, organisation_id: str, project_id: str) -> MonitoringProject | None:
        project = self.db.get(MonitoringProject, project_id)
        if project is None or project.organisation_id != organisation_id:
            return None
        return project

    def record_snapshots(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        project_id: str,
        metrics: list[dict[str, Any]],
        created_by: str | None = None,
        emit_learning: bool = True,
    ) -> dict[str, Any]:
        project = self.get_project(organisation_id=organisation_id, project_id=project_id)
        if project is None:
            raise LookupError("Monitoring project not found")
        if not metrics:
            raise ValueError("At least one metric is required")

        now = datetime.now(UTC)
        created: list[dict[str, Any]] = []
        learning_hooks: list[dict[str, Any]] = []
        for item in metrics:
            key = str(item.get("metric_key") or "").strip()
            if not key:
                raise ValueError("metric_key is required")
            value = float(item["metric_value"])
            captured = item.get("captured_at")
            if isinstance(captured, str):
                captured_at = datetime.fromisoformat(captured.replace("Z", "+00:00"))
            elif isinstance(captured, datetime):
                captured_at = captured
            else:
                captured_at = now

            # Historical delta vs previous snapshot for this key
            previous = self.db.scalar(
                select(MetricSnapshot)
                .where(
                    MetricSnapshot.monitoring_project_id == project_id,
                    MetricSnapshot.organisation_id == organisation_id,
                    MetricSnapshot.metric_key == key,
                )
                .order_by(MetricSnapshot.captured_at.desc())
                .limit(1)
            )
            row = MetricSnapshot(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                monitoring_project_id=project_id,
                metric_key=key,
                metric_value=value,
                captured_at=captured_at,
            )
            self.db.add(row)
            delta = None if previous is None else value - float(previous.metric_value)
            created.append(
                {
                    "id": row.id,
                    "metric_key": key,
                    "metric_value": value,
                    "captured_at": captured_at.isoformat(),
                    "delta": delta,
                }
            )
            if emit_learning and previous is not None and abs(delta or 0) >= 0.01:
                learning_hooks.append(
                    {
                        "metric_key": key,
                        "previous": float(previous.metric_value),
                        "current": value,
                        "delta": delta,
                        "project_id": project_id,
                        "website_id": project.website_id,
                    }
                )

        self.db.commit()
        learning_record_ids = []
        if learning_hooks:
            learning_record_ids = self._emit_learning_records(
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                hooks=learning_hooks,
                created_by=created_by,
            )
        return {
            "project_id": project_id,
            "snapshots": created,
            "learning_hooks": learning_hooks,
            "learning_record_ids": learning_record_ids,
        }

    def list_snapshots(
        self, *, organisation_id: str, project_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        project = self.get_project(organisation_id=organisation_id, project_id=project_id)
        if project is None:
            raise LookupError("Monitoring project not found")
        rows = list(
            self.db.scalars(
                select(MetricSnapshot)
                .where(
                    MetricSnapshot.monitoring_project_id == project_id,
                    MetricSnapshot.organisation_id == organisation_id,
                )
                .order_by(MetricSnapshot.captured_at.desc())
                .limit(limit)
            )
        )
        return [
            {
                "id": r.id,
                "metric_key": r.metric_key,
                "metric_value": r.metric_value,
                "captured_at": r.captured_at.isoformat() if r.captured_at else None,
            }
            for r in rows
        ]

    def record_search_performance(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        project_id: str,
        clicks: int,
        impressions: int,
        ctr: float | None = None,
        avg_position: float | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        project = self.get_project(organisation_id=organisation_id, project_id=project_id)
        if project is None:
            raise LookupError("Monitoring project not found")
        now = datetime.now(UTC)
        if ctr is None and impressions > 0:
            ctr = clicks / impressions
        row = SearchPerformanceSnapshot(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=project.website_id,
            monitoring_project_id=project_id,
            clicks=clicks,
            impressions=impressions,
            ctr=ctr,
            avg_position=avg_position,
            captured_at=now,
        )
        self.db.add(row)
        self.db.commit()
        return {
            "id": row.id,
            "clicks": clicks,
            "impressions": impressions,
            "ctr": ctr,
            "avg_position": avg_position,
            "captured_at": now.isoformat(),
        }

    def anomaly_observations(self, *, organisation_id: str, project_id: str) -> list[dict[str, Any]]:
        """Build anomaly-engine MetricObservation payloads from snapshot history."""
        rows = list(
            self.db.scalars(
                select(MetricSnapshot)
                .where(
                    MetricSnapshot.monitoring_project_id == project_id,
                    MetricSnapshot.organisation_id == organisation_id,
                )
                .order_by(MetricSnapshot.metric_key.asc(), MetricSnapshot.captured_at.asc())
            )
        )
        by_key: dict[str, list[tuple[datetime, float]]] = {}
        for row in rows:
            by_key.setdefault(row.metric_key, []).append((row.captured_at, float(row.metric_value)))
        observations = []
        for key, points in by_key.items():
            if len(points) < 2:
                continue
            observations.append(
                {
                    "metric_key": key,
                    "anomaly_type": "metric_shift",
                    "points": [(ts.isoformat(), val) for ts, val in points],
                    "label_hint": f"monitoring:{project_id}:{key}",
                }
            )
        return observations

    def _emit_learning_records(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        hooks: list[dict[str, Any]],
        created_by: str | None,
    ) -> list[str]:
        """Bridge material monitoring deltas into Learning Engine 2.0 records."""
        try:
            from learning_engine2.learning import LearningRecordView, OutcomeUpdate
            from learning_engine2.models import Learning2CreateSpec
            from learning_engine2.service import LearningEngine2Service
        except Exception:  # noqa: BLE001
            return []

        svc = LearningEngine2Service(self.db)
        ids: list[str] = []
        for hook in hooks:
            score = max(0.0, min(100.0, 50.0 + float(hook["delta"]) * 10.0))
            try:
                from learning_engine2.learning import ExecutionUpdate

                report = svc.create_record(
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    spec=Learning2CreateSpec(
                        website_id=str(hook["website_id"]),
                        view=LearningRecordView(
                            name=f"Monitor {hook['metric_key']}",
                            industry="general",
                            record_status="proposed",
                            context_summary=(
                                f"Monitoring project {hook['project_id']} observed "
                                f"{hook['metric_key']} {hook['previous']} → {hook['current']}"
                            ),
                            recommendation_text=(
                                f"Investigate and respond to {hook['metric_key']} delta "
                                f"of {hook['delta']}"
                            ),
                            expected_impact="stabilise_or_improve_metric",
                            expected_impact_score=score,
                            confidence=0.6,
                            execution_summary=None,
                            execution_status=None,
                            actual_outcome=None,
                            actual_outcome_score=None,
                            outcome_delta=None,
                            topic_key=str(hook["metric_key"]),
                            format_key="monitoring_snapshot",
                            source_key="monitoring_engine",
                            writer_key=None,
                            intervention_key="monitor_respond",
                            engine_key=None,
                            context_factors=[],
                            not_universal_geo_strategy=True,
                            not_universal_geo_note="Monitoring deltas are not universal GEO strategy.",
                        ),
                        notes="auto_from_monitoring",
                    ),
                )
                svc.record_execution(
                    organisation_id=organisation_id,
                    record_id=report.record_id,
                    update=ExecutionUpdate(
                        execution_summary=f"Observed monitoring delta for {hook['metric_key']}",
                        execution_status="executed",
                    ),
                )
                svc.record_outcome(
                    organisation_id=organisation_id,
                    record_id=report.record_id,
                    update=OutcomeUpdate(
                        actual_outcome="observed_metric_delta",
                        actual_outcome_score=score,
                    ),
                )
                ids.append(report.record_id)
            except Exception:  # noqa: BLE001
                continue
        return ids
