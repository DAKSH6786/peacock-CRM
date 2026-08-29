from __future__ import annotations

from peacock_opportunity import build_opportunity, peacock_impact_score, rank_opportunities


def test_peacock_impact_score_formula() -> None:
    score = peacock_impact_score(
        visibility_opportunity=0.5, business_relevance=0.8, competitive_gap=0.6, confidence=0.9, implementation_difficulty=2.0
    )
    expected = round(min(100.0, (0.5 * 0.8 * 0.6 * 0.9 / 2.0) * 100.0), 2)
    assert score == expected


def test_rank_opportunities_orders_by_impact_descending() -> None:
    opp_low = build_opportunity(
        action="Low", reason="r", affected_page="/a", seo_opportunity="Low", aeo_opportunity="Low", geo_opportunity="Low",
        ai_visibility_opportunity="Low", business_value="Low", competitor_gap="Low", implementation_difficulty="High", confidence="experimental",
    )
    opp_high = build_opportunity(
        action="High", reason="r", affected_page="/b", seo_opportunity="Critical", aeo_opportunity="High", geo_opportunity="High",
        ai_visibility_opportunity="High", business_value="High", competitor_gap="High", implementation_difficulty="Low", confidence="high",
    )
    ranked = rank_opportunities([opp_low, opp_high], limit=10)
    assert ranked[0].action == "High"
    assert ranked[0].peacock_impact_score >= ranked[1].peacock_impact_score


def test_measurement_engine_never_fabricates_external_metrics() -> None:
    from measurement import capture_snapshot, compare_snapshots, get_history

    url = "https://example-measurement-test.com/"
    capture_snapshot(url=url, seo_score=50, aeo_score=40, geo_score=30, information_gain_score=20, word_count=400, content_hash="a", citations_count=0)
    comparison_single = compare_snapshots(url)
    assert comparison_single.period_label == "insufficient_history"

    capture_snapshot(url=url, seo_score=60, aeo_score=45, geo_score=35, information_gain_score=25, word_count=450, content_hash="b", citations_count=1)
    comparison = compare_snapshots(url)
    assert comparison.period_label != "insufficient_history"
    for metric_value in comparison.external_metrics.values():
        assert metric_value == "Data unavailable — connector required"
    assert len(get_history(url)) == 2


def test_content_decay_detector_flags_real_score_drop() -> None:
    from measurement import capture_snapshot, detect_content_decay

    url = "https://example-decay-test.com/"
    capture_snapshot(url=url, seo_score=80, aeo_score=70, geo_score=60, information_gain_score=50, word_count=500, content_hash="a", citations_count=2)
    capture_snapshot(url=url, seo_score=60, aeo_score=55, geo_score=45, information_gain_score=35, word_count=500, content_hash="a", citations_count=2)
    refresh = detect_content_decay(url)
    assert refresh is not None
    assert "seo_score" in refresh.declining_metrics
