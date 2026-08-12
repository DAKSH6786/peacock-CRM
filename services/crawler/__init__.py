"""Peacock Crawler — website ingestion and crawling subsystem."""

from crawler.engine import PeacockCrawler
from crawler.policy import CrawlPolicy, POLICY_PRESETS, resolve_policy
from crawler.ports import CrawlProgress, FetchResult
from crawler.service import CrawlerService
from crawler.store import InMemoryCrawlStore, StoredCrawl, StoredIssue, StoredPage

__all__ = [
    "CrawlPolicy",
    "CrawlProgress",
    "CrawlerService",
    "FetchResult",
    "InMemoryCrawlStore",
    "POLICY_PRESETS",
    "PeacockCrawler",
    "StoredCrawl",
    "StoredIssue",
    "StoredPage",
    "resolve_policy",
]
