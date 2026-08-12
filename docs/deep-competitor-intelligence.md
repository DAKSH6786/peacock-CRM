# Deep Competitor Intelligence

Do **not** limit competitor analysis to four manually entered domains.

## Competitor categories

A website may be a strong SEO competitor without being a direct business competitor.

| Category | Typical signal |
| --- | --- |
| Business Competitor | product similarity |
| Search Competitor | keyword overlap |
| Content Competitor | topic overlap |
| AI Visibility Competitor | AI mention overlap |
| Citation Competitor | citation overlap |
| Entity Competitor | entity similarity |
| SERP Competitor | SERP overlap |

## Automatic discovery

Dynamic discovery uses:

- SERP overlap
- keyword overlap
- topic overlap
- AI mention overlap
- citation overlap
- entity similarity
- product similarity

Candidates are classified into one or more categories automatically.

## Competitive Delta Engine

For each rival dimension, Peacock answers:

1. **Where are they stronger?**
2. **Why?**
3. **How difficult is the gap?**
4. **What would close it?**
5. **What would leapfrog them?**

## Reverse-engineer winning content

When a competitor repeatedly performs better, compare evidence on:

topical completeness · entities · structure · freshness · original data · references ·
schema · internal linking · backlinks · citations · author signals · content type ·
intent satisfaction · page UX

Returns **evidence-backed differences** and **differentiated** recommendations.

## Do not copy competitor content

`copy_competitor_content_rejected = true`

Forbidden recommendation modes:

- copy_competitor_content
- paraphrase_competitor_page
- scrape_and_republish
- thin_rewrite_of_competitor

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/deep-competitors/catalog` | Categories, signals, forbidden modes |
| `POST` | `/deep-competitors/analyses` | Discover + deltas + content diffs + strategy |
| `GET` | `/deep-competitors/analyses/{id}` | Retrieve report |
