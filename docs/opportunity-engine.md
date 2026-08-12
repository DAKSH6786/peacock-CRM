# Peacock Opportunity Engine

Always-running intelligence layer: **Peacock Opportunities**.

## Example opportunity types

- Competitor gained AI visibility
- New citation source emerged
- High-value topic became available
- Existing article is decaying
- Entity relationship weakened
- New prompt cluster appeared
- Competitor content is outdated
- AI sentiment changed
- Backlink source gained influence
- Search demand shifted
- AI answer changed materially

## Opportunity fields

| Field | Role |
| --- | --- |
| Opportunity | Type + title + description |
| Evidence | Supporting statements / sources |
| Impact | Business / visibility stakes (0–100) |
| Urgency | Time sensitivity (0–100) |
| Confidence | Signal trust (0–100) |
| Difficulty | Effort to capture (0–100; inverted in rank) |
| Expected Value | Anticipated upside (0–100) |
| Recommended Action | Concrete next step |

## Opportunity ranking

**Do not use one manually weighted formula forever.**

1. **Start explainable** — transparent contributions from impact, urgency, confidence, expected value, difficulty
2. **Then adapt** — historical realized outcomes adjust feature weights (`base` → `blended` → more `learned`)
3. Every scan sets `fixed_formula_rejected=true` and stores weight snapshots + per-opportunity factor breakdowns

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/opportunities/catalog` | Types, features, methodology |
| `POST` | `/opportunities/scans` | Run / refresh opportunity scan |
| `GET` | `/opportunities/scans/{id}` | Retrieve ranked opportunities |
| `POST` | `/opportunities/outcomes` | Record realized outcome (improves ranking) |

## Tables

`opportunity_scans`, `peacock_opportunities`, `po_evidence`, `po_ranking_factors`, `po_ranking_weights`, `po_outcome_feedback`
