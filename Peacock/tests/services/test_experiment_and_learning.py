from __future__ import annotations

from experiment_engine import evaluate_experiment, log_experiment
from measurement import capture_snapshot
from peacock_learning import confidence_for_type, log_recommendation, record_result


def test_experiment_engine_reports_causality_caution() -> None:
    url = "https://example-experiment-test.com/"
    capture_snapshot(url=url, seo_score=50, aeo_score=40, geo_score=30, information_gain_score=20, word_count=300, content_hash="a", citations_count=0)
    experiment = log_experiment(hypothesis="Adding FAQ improves AEO", page_url=url, change_description="Added FAQ", change_category="answer_blocks")
    capture_snapshot(url=url, seo_score=55, aeo_score=60, geo_score=40, information_gain_score=25, word_count=350, content_hash="b", citations_count=1)
    evaluated = evaluate_experiment(experiment.experiment_id)
    assert evaluated.status in {"completed", "inconclusive"}
    assert "does not by itself prove" in evaluated.causality_caution


def test_learning_engine_confidence_requires_history() -> None:
    adjustment = confidence_for_type("nonexistent_type_xyz")
    assert adjustment.historical_sample_size == 0
    assert adjustment.adjusted_confidence == "experimental"


def test_learning_engine_tracks_outcome_and_adjusts_confidence() -> None:
    rec = log_recommendation(
        recommendation="Add schema", recommendation_type="schema_test_type", page_url="https://example.com/", baseline_score=50, confidence_at_log_time="medium"
    )
    record_result(rec.record_id, day_bucket=30, score=70)
    assert rec.outcome == "improved"

    rec2 = log_recommendation(
        recommendation="Add schema", recommendation_type="schema_test_type", page_url="https://example.com/other", baseline_score=50, confidence_at_log_time="medium"
    )
    record_result(rec2.record_id, day_bucket=30, score=71)
    rec3 = log_recommendation(
        recommendation="Add schema", recommendation_type="schema_test_type", page_url="https://example.com/third", baseline_score=50, confidence_at_log_time="medium"
    )
    record_result(rec3.record_id, day_bucket=30, score=72)

    adjustment = confidence_for_type("schema_test_type")
    assert adjustment.historical_sample_size == 3
    assert adjustment.historical_hit_rate == 1.0
    assert adjustment.adjusted_confidence == "high"
    assert "does not prove causation" in adjustment.caution
