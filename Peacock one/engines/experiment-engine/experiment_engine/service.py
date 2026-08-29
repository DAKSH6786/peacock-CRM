"""Experiment Engine service — in-memory (process-local; see measurement.store note)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from measurement.service import compare_snapshots
from measurement.store import latest

from experiment_engine.models import Experiment

_EXPERIMENTS: dict[str, Experiment] = {}


def log_experiment(
    *,
    hypothesis: str,
    page_url: str,
    change_description: str,
    change_category: str = "other",
) -> Experiment:
    baseline = latest(page_url)
    experiment = Experiment(
        experiment_id=str(uuid4()),
        hypothesis=hypothesis,
        page_url=page_url,
        change_description=change_description,
        change_category=change_category,
        baseline_snapshot_at=baseline.captured_at.isoformat() if baseline else None,
        start_date=datetime.now(tz=UTC).isoformat(),
        status="running",
    )
    _EXPERIMENTS[experiment.experiment_id] = experiment
    return experiment


def evaluate_experiment(experiment_id: str) -> Experiment:
    experiment = _EXPERIMENTS.get(experiment_id)
    if experiment is None:
        raise KeyError(f"Unknown experiment: {experiment_id}")

    comparison = compare_snapshots(experiment.page_url, period="custom", custom_days=0)
    if comparison.period_label == "insufficient_history":
        experiment.status = "running"
        experiment.outcome_summary = (
            "Not enough re-analysis snapshots yet to evaluate this experiment — re-run the analysis "
            "on this page again after the change has had time to take effect."
        )
        return experiment

    improved = [d.metric for d in comparison.deltas if d.absolute_delta and d.absolute_delta > 0]
    declined = [d.metric for d in comparison.deltas if d.absolute_delta and d.absolute_delta < 0]

    experiment.comparison_snapshot_at = comparison.latest_captured_at
    if improved and not declined:
        experiment.status = "completed"
        experiment.outcome_summary = f"Improved: {', '.join(improved)}. {experiment.causality_caution}"
    elif declined and not improved:
        experiment.status = "completed"
        experiment.outcome_summary = f"Declined: {', '.join(declined)}. {experiment.causality_caution}"
    else:
        experiment.status = "inconclusive"
        experiment.outcome_summary = (
            f"Mixed result — improved: {', '.join(improved) or 'none'}; declined: {', '.join(declined) or 'none'}. "
            f"{experiment.causality_caution}"
        )
    return experiment


def get_experiment(experiment_id: str) -> Experiment | None:
    return _EXPERIMENTS.get(experiment_id)


def list_experiments(page_url: str | None = None) -> list[Experiment]:
    values = list(_EXPERIMENTS.values())
    if page_url:
        values = [e for e in values if e.page_url == page_url]
    return sorted(values, key=lambda e: e.start_date, reverse=True)
