"""Regression tests for final-audit honesty fixes and crawler SSRF protection."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from crawler.engine import PeacockCrawler
from crawler.policy import CrawlPolicy
from crawler.url_utils import UrlValidationError, assert_public_crawl_target, is_blocked_crawl_host
from geo_engine import GeoEngine, ProbabilisticVisibilityService
from seo_engine import SeoEngine
from strategy_engine import StrategyEngine


def test_scaffold_engines_are_not_ready_when_unimplemented() -> None:
    assert StrategyEngine("org").status()["ready"] is False
    assert StrategyEngine("org").status()["features_implemented"] is False


def test_geo_and_seo_status_disclose_io_modes() -> None:
    geo = GeoEngine("org").status()
    assert geo["features_implemented"] is True
    assert geo["live_engine_probes"] is True
    seo = SeoEngine("org").status()
    assert seo["connector_mode"] == "mock_by_default"
    assert seo["live_connectors"] is False


def test_ssrf_blocks_private_and_metadata_hosts() -> None:
    assert is_blocked_crawl_host("localhost")
    assert is_blocked_crawl_host("127.0.0.1")
    assert is_blocked_crawl_host("10.0.0.8")
    assert is_blocked_crawl_host("192.168.1.1")
    assert is_blocked_crawl_host("169.254.169.254")
    assert is_blocked_crawl_host("metadata.google.internal")
    assert not is_blocked_crawl_host("example.com")
    with pytest.raises(UrlValidationError):
        assert_public_crawl_target("127.0.0.1")
    with pytest.raises(UrlValidationError):
        assert_public_crawl_target("example.com", resolved_ips=["10.1.2.3"])


@pytest.mark.asyncio
async def test_crawler_rejects_private_seed_by_default() -> None:
    crawler = PeacockCrawler()
    with pytest.raises(UrlValidationError, match="Blocked crawl target"):
        await crawler.start(
            organisation_id="org",
            workspace_id="ws",
            seed_url="http://127.0.0.1:9/",
            policy=CrawlPolicy(max_pages=1, allow_private_hosts=False, require_dns=False),
        )


def test_crawler_service_status_does_not_crash_with_slots() -> None:
    from crawler import CrawlerService

    status = CrawlerService("org").status()
    assert status["ready"] is True
    assert status["ssrf_protection"] is True


def test_invalid_peacock_mode_raises_clear_value_error() -> None:
    from intelligence.peacock_modes import resolve_mode

    with pytest.raises(ValueError, match="Invalid peacock_mode"):
        resolve_mode(explicit="balanced")


@pytest.mark.asyncio
async def test_visibility_refuses_gateway_without_instance() -> None:
    class _Session:
        def get(self, *_args, **_kwargs):  # noqa: ANN001
            return SimpleNamespace(
                organisation_id="org",
                workspace_id="ws",
                brand_name="Acme",
                notes="COMPETITORS:Rival",
                max_calls_per_minute=6,
                max_concurrent=1,
                max_total_calls=50,
                min_interval_ms=1500,
                target_repetitions=5,
                max_repetitions=20,
                cells=[],
                campaign_status="draft",
            )

        def commit(self) -> None:
            return None

    svc = ProbabilisticVisibilityService(_Session())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match="LLMGateway"):
        await svc.run_campaign(
            campaign_id="camp",
            organisation_id="org",
            use_mock=False,
            gateway=None,
        )
