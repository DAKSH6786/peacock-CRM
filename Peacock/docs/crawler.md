# Peacock Crawler

Website ingestion and crawling subsystem for Peacock One.

## Responsibilities

Given a seed URL such as `https://example.com`, Peacock Crawler:

1. Validates the domain and normalises the URL
2. Inspects `robots.txt`
3. Discovers and parses sitemaps
4. Crawls internal pages up to a configurable policy limit
5. Detects redirect chains, broken pages, canonical tags, JS-heavy pages
6. Extracts metadata, content, headings, structured data, links, images/ALT, word counts, language, content type, content hash, crawl depth
7. Flags duplicate / near-duplicate content and orphan candidates
8. Optionally renders with Playwright when pages look JS-heavy

## Crawl policies (not commercial plans)

Commercial tiers map to `CrawlPolicy` **outside** the engine:

| Preset (API/billing) | Default `max_pages` |
| --- | --- |
| `free_trial` | 100 |
| `starter` | 1,000 |
| `pro` | 10,000 |
| `enterprise` | configurable via `max_pages` |

The engine only accepts a `CrawlPolicy` object. See `services/crawler/policy.py`.

## Controls

- Progress: pages discovered / crawled / failed, issues found, progress %
- Pause / resume / cancel / restart / retry failed URLs

## API

- `POST /websites` — ingest URL
- `POST /crawls` — start crawl (`policy_preset`, `max_pages`, `policy` overrides)
- `GET /crawls/{id}` / `GET /crawls/{id}/progress`
- `POST /crawls/{id}/pause|resume|cancel|restart|retry-failed`

## Page storage

Each `crawl_pages` row stores URL, canonical, status_code, title, meta_description, h1/h2/h3, body_text, word_count, internal/external links, images, schema, robots, indexability, crawl_depth, content_hash, plus link rows in `crawl_links`.
