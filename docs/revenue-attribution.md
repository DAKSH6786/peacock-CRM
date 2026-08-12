# Peacock Revenue Attribution

Connects **visibility to business value** — competitors often stop at visibility.

## Funnel map

```
Recommendation
        ↓
Content
        ↓
Visibility
        ↓
Traffic
        ↓
Lead
        ↓
Conversion
        ↓
Revenue
```

## Integrations (where available)

GA4 · CRM · Search Console · Conversions · Pipeline · Transactions · Leads · Peacock internal

Missing sources widen uncertainty and lower causality claims.

## Uncertainty & causality

- Attributed revenue is a **range**, not a point forecast.
- Every stage and chain link carries **uncertainty**.
- Causality levels: `insufficient_data` · `correlation` · `likely_contribution` · `multi_touch_model` · `causal_evidence`
- **Do not overclaim causality** — the engine never auto-concludes that visibility alone caused revenue.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/revenue-attribution/catalog` | Funnel, sources, causality warning |
| `POST` | `/revenue-attribution/analyses` | Run attribution |
| `GET` | `/revenue-attribution/analyses/{id}` | Retrieve |

## Tables

`revenue_attribution_analyses`, `ra_funnel_stages`, `ra_chain_links`, `ra_source_snapshots`
