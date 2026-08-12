"""Comprehensive Peacock Crawler tests against a local mock website."""

from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import pytest

from crawler.engine import PeacockCrawler
from crawler.extract import extract_page, near_duplicate
from crawler.policy import POLICY_PRESETS, CrawlPolicy, resolve_policy
from crawler.sitemap import parse_sitemap_xml
from crawler.store import InMemoryCrawlStore
from crawler.url_utils import UrlValidationError, normalise_url, validate_domain


MOCK_PAGES: dict[str, tuple[int, str, dict[str, str]]] = {}


def _build_site() -> None:
    home = """<!doctype html>
<html lang="en">
<head>
  <title>Mock Home</title>
  <meta name="description" content="Home description" />
  <link rel="canonical" href="/"/>
  <script type="application/ld+json">{"@type":"Organization","name":"MockCo"}</script>
</head>
<body>
  <h1>Welcome</h1>
  <h2>Section</h2>
  <h3>Detail</h3>
  <p>Alpha content about visibility intelligence and crawling.</p>
  <a href="/about">About</a>
  <a href="/broken">Broken</a>
  <a href="/dup">Dup A</a>
  <a href="/js">JS App</a>
  <a href="/redirect">Redirect</a>
  <a href="https://external.example/out">Outbound</a>
  <img src="/logo.png" alt="Logo"/>
</body>
</html>"""
    about = """<!doctype html>
<html lang="en"><head><title>About</title>
<meta name="robots" content="index,follow"/>
</head>
<body><h1>About</h1><p>About page with enough words for language detection and the and with for.</p>
<a href="/">Home</a><a href="/orphan-linked">Linked</a>
</body></html>"""
    dup = """<!doctype html><html lang="en"><head><title>Dup</title></head>
<body><h1>Welcome</h1><h2>Section</h2><h3>Detail</h3>
<p>Alpha content about visibility intelligence and crawling.</p></body></html>"""
    js_heavy = """<!doctype html><html><head><title>App</title>
<script src="/app.react.js"></script><script src="/chunk1.js"></script>
<script src="/chunk2.js"></script><script src="/chunk3.js"></script>
<script src="/chunk4.js"></script><script src="/chunk5.js"></script>
<script src="/chunk6.js"></script><script src="/chunk7.js"></script>
<script src="/chunk8.js"></script>
</head><body><div id="root"></div></body></html>"""
    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>http://HOST/</loc></url>
  <url><loc>http://HOST/about</loc></url>
  <url><loc>http://HOST/js</loc></url>
  <url><loc>http://HOST/sitemap-only</loc></url>
</urlset>"""
    robots = "User-agent: *\nAllow: /\nSitemap: http://HOST/sitemap.xml\n"
    MOCK_PAGES.clear()
    MOCK_PAGES.update(
        {
            "/": (200, home, {"Content-Type": "text/html"}),
            "/about": (200, about, {"Content-Type": "text/html"}),
            "/dup": (200, dup, {"Content-Type": "text/html"}),
            "/js": (200, js_heavy, {"Content-Type": "text/html"}),
            "/sitemap-only": (
                200,
                "<html><head><title>Sitemap Only</title></head><body><h1>Orphanish</h1><p>Only in sitemap.</p></body></html>",
                {"Content-Type": "text/html"},
            ),
            "/broken": (404, "<html><body>missing</body></html>", {"Content-Type": "text/html"}),
            "/redirect": (302, "", {"Location": "/about"}),
            "/sitemap.xml": (200, sitemap, {"Content-Type": "application/xml"}),
            "/robots.txt": (200, robots, {"Content-Type": "text/plain"}),
            "/malformed": (200, "<html><title>Broken<script></title><p>still ok", {"Content-Type": "text/html"}),
        }
    )


class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path or "/"
        if path not in MOCK_PAGES:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found")
            return
        status, body, headers = MOCK_PAGES[path]
        if status in {301, 302, 307, 308}:
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            return
        payload = body
        if path in {"/sitemap.xml", "/robots.txt"}:
            host = self.headers.get("Host", "127.0.0.1")
            payload = body.replace("HOST", host)
        data = payload.encode("utf-8")
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


@pytest.fixture()
def mock_site():
    _build_site()
    server = ThreadingHTTPServer(("127.0.0.1", 0), MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    yield base
    server.shutdown()
    server.server_close()


def test_validate_and_normalise_url() -> None:
    assert validate_domain("Example.COM") == "example.com"
    norm = normalise_url("HTTPS://Example.com:443/a/b/?b=2&a=1#frag")
    assert norm.normalised == "https://example.com/a/b?a=1&b=2"
    with pytest.raises(UrlValidationError):
        normalise_url("ftp://example.com")


def test_policy_presets_are_outside_engine_defaults() -> None:
    assert POLICY_PRESETS["free_trial"].max_pages == 100
    assert POLICY_PRESETS["starter"].max_pages == 1_000
    assert POLICY_PRESETS["pro"].max_pages == 10_000
    enterprise = resolve_policy(preset="enterprise", max_pages=42_000)
    assert enterprise.max_pages == 42_000
    # Engine default remains modest and plan-agnostic
    assert CrawlPolicy().max_pages == 100


def test_parse_sitemap_and_extract_page() -> None:
    pages, nested = parse_sitemap_xml(
        """<?xml version="1.0"?><urlset><url><loc>https://example.com/a</loc></url></urlset>"""
    )
    assert pages == ["https://example.com/a"]
    assert nested == []
    extraction = extract_page(
        request_url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        html="<html lang='en'><head><title>T</title><meta name='description' content='D'/>"
        "<link rel='canonical' href='https://example.com/'/>"
        "<script type='application/ld+json'>{\"@type\":\"WebPage\"}</script></head>"
        "<body><h1>H</h1><h2>S</h2><a href='/b'>B</a><img src='/i.png' alt='x'/>"
        "<p>the and with for words</p></body></html>",
        headers={"Content-Type": "text/html"},
        seed_host_url="https://example.com/",
    )
    assert extraction.title == "T"
    assert extraction.meta_description == "D"
    assert extraction.h1 == ["H"]
    assert extraction.images[0].alt == "x"
    assert extraction.schema_blocks[0]["@type"] == "WebPage"
    assert extraction.word_count > 0
    assert extraction.content_hash


def test_near_duplicate_detection() -> None:
    assert near_duplicate(
        "Alpha content about visibility intelligence and crawling.",
        "Alpha content about visibility intelligence and crawling!",
        threshold=0.9,
    )


@pytest.mark.asyncio
async def test_peacock_crawler_against_mock_site(mock_site: str) -> None:
    store = InMemoryCrawlStore()
    crawler = PeacockCrawler(store=store)
    policy = CrawlPolicy(
        max_pages=20,
        max_depth=3,
        require_dns=False,
        allow_js_render=False,
        discover_sitemaps=True,
        parse_sitemaps=True,
        near_duplicate_threshold=0.55,
    )
    crawl = await crawler.start(
        organisation_id="org",
        workspace_id="ws",
        seed_url=mock_site + "/",
        policy=policy,
    )
    assert crawl.status == "completed"
    assert crawl.progress.pages_crawled >= 3
    assert crawl.progress.pages_discovered >= crawl.progress.pages_crawled
    assert crawl.progress.progress_percent > 0

    home = next(p for p in crawl.pages.values() if p.url.rstrip("/").endswith(f"{urlparse(mock_site).netloc}") or p.url.endswith("/"))
    # Find home by title
    home = next(p for p in crawl.pages.values() if p.title == "Mock Home")
    assert home.meta_description == "Home description"
    assert home.h1 == ["Welcome"]
    assert home.h2 == ["Section"]
    assert home.h3 == ["Detail"]
    assert home.word_count > 0
    assert home.content_hash
    assert any("/about" in link for link in home.internal_links)
    assert any("external.example" in link for link in home.external_links)
    assert any((img.get("alt") == "Logo") for img in home.images)
    assert home.schema
    assert home.canonical
    assert home.indexability
    assert home.crawl_depth == 0

    broken = next((p for p in crawl.pages.values() if p.status_code == 404), None)
    assert broken is not None
    assert any(i.code == "broken_page" for i in crawl.issues)

    assert any(p.is_js_heavy for p in crawl.pages.values())
    assert any(i.code == "js_heavy_page" for i in crawl.issues)
    assert any(p.is_near_duplicate for p in crawl.pages.values())
    assert any(i.code in {"duplicate_content", "near_duplicate_content"} for i in crawl.issues)
    assert crawl.sitemap_urls
    assert any("sitemap.xml" in url for url in crawl.sitemap_urls)


@pytest.mark.asyncio
async def test_crawl_respects_max_pages_limit(mock_site: str) -> None:
    crawler = PeacockCrawler()
    crawl = await crawler.start(
        organisation_id="org",
        workspace_id="ws",
        seed_url=mock_site + "/",
        policy=CrawlPolicy(max_pages=2, max_depth=5, allow_js_render=False),
    )
    assert crawl.progress.pages_crawled <= 2
    assert crawl.status == "completed"


@pytest.mark.asyncio
async def test_malformed_html_does_not_crash_worker(mock_site: str) -> None:
    crawler = PeacockCrawler()
    crawl = await crawler.start(
        organisation_id="org",
        workspace_id="ws",
        seed_url=mock_site + "/malformed",
        policy=CrawlPolicy(max_pages=1, discover_sitemaps=False, allow_js_render=False),
    )
    assert crawl.status == "completed"
    assert crawl.progress.pages_crawled == 1


@pytest.mark.asyncio
async def test_pause_cancel_restart_retry_controls(mock_site: str) -> None:
    store = InMemoryCrawlStore()
    crawler = PeacockCrawler(store=store)
    # Seed a completed crawl with a failed page for retry
    crawl = await crawler.start(
        organisation_id="org",
        workspace_id="ws",
        seed_url=mock_site + "/broken",
        policy=CrawlPolicy(max_pages=1, discover_sitemaps=False, allow_js_render=False, max_retries_per_url=0),
    )
    assert crawl.progress.pages_failed >= 1 or any(p.status_code == 404 for p in crawl.pages.values())

    paused = crawler.pause(crawl.id)
    assert paused.status == "paused"
    resumed = crawler.resume(crawl.id)
    assert resumed.status == "running"
    cancelled = crawler.cancel(crawl.id)
    assert cancelled.status == "cancelled"

    restarted = await crawler.restart(crawl.id, organisation_id="org", workspace_id="ws")
    assert restarted.id != crawl.id
    assert restarted.status == "completed"

    retried = await crawler.retry_failed(restarted.id)
    assert retried.status == "completed"
