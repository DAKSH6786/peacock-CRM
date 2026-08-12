# Peacock SEO Engine

Transforms Peacock Crawler output into an actionable SEO audit.

## Principles

- **Deterministic metrics dominate numeric scores.** LLMs may only provide interpretation.
- External connectors (PageSpeed, Core Web Vitals, Search Console, Analytics) are **optional**.
- Local development uses **mock adapters** that implement the same ports.

## Analyses

| Area | Signals |
| --- | --- |
| Crawlability | robots.txt, sitemap, status codes, redirects, canonicalisation, indexability |
| Metadata | missing/duplicate/short/long titles, missing/duplicate descriptions |
| Content | thin pages, duplicates, heading problems, structure, freshness, topic overlap, cannibalisation |
| Internal linking | orphans, low-link pages, depth, broken links, over-linking |
| Images | missing ALT, oversized heuristics, broken image refs |
| Structured data | presence, basic JSON-LD validation, opportunities |
| Performance | JS-heavy crawl heuristics + optional PageSpeed/CWV connectors |

## Scores (0–100)

Each score includes: `score`, `confidence`, `inputs_used`, `major_positive_factors`, `major_negative_factors`, `recommended_actions`.

- Technical SEO
- Content Quality
- On-Page SEO
- Internal Linking
- Structured Data
- Performance
- Indexability
- **Peacock SEO Score** — fixed weighted rollup (`packages/scoring/PEACOCK_SEO_WEIGHTS`)

## Recommendations

Each recommendation includes: `priority`, `impact`, `effort`, `confidence`, `affected_pages`, `reason`, `suggested_fix`, plus deterministic `priority_score`.

## API

- `POST /seo/audits` `{ crawl_id, fetch_connectors?, persist? }`
- `GET /seo/audits/{id}` / `GET /seo/audits/{id}/overview`

## UI

Audit Overview, Critical Issues, Warnings, Opportunities, Page-level Issues, Recommendations.
