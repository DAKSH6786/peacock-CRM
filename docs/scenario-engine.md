# Peacock Scenario Engine

Counterfactual strategy comparison with **projected ranges** (not fake precision).

## Strategies compared

| Code | Label |
| --- | --- |
| `do_nothing` | Do nothing (baseline) |
| `fix_technical_seo` | Fix technical SEO |
| `publish_more_content` | Publish more content |
| `refresh_existing_content` | Refresh existing content |
| `build_topical_authority` | Build topical authority |
| `build_third_party_authority` | Build third-party authority |
| `seo_only` | SEO-only strategy |
| `geo_only` | GEO-only strategy |
| `seo_aeo_geo` | SEO + AEO + GEO |
| `peacock_recommended` | Peacock recommended strategy |

## Example — Projected 90-Day Organic Visibility

| Scenario | Range |
| --- | --- |
| Baseline | +0% to +4% |
| Content Expansion | +7% to +18% |
| Authority Strategy | +9% to +22% |
| Peacock Strategy | +14% to +31% |

Every scenario includes:

- **confidence**
- **assumptions**
- **data quality**
- **uncertainty**

Point forecasts are intentionally avoided (`ranges_not_fake_precision=true`).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/scenarios/catalog` | Strategies, example comparison, methodology |
| `POST` | `/scenarios/analyses` | Run counterfactual comparison |
| `GET` | `/scenarios/analyses/{id}` | Retrieve analysis |

## Tables

`scenario_analyses`, `se_scenarios`, `se_metric_ranges`, `se_assumptions`
