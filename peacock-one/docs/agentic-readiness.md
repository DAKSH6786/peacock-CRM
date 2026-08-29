# Peacock Agentic Web Readiness

Prepares Peacock One for **agentic search** by measuring whether a business is
**machine-operable**.

## Agent Discoverability

Potential checks:

| Check | Purpose |
| --- | --- |
| Structured product information | Attributes agents can parse |
| Clear pricing | Unambiguous price extraction |
| Availability | Stock / availability states |
| Product IDs | Stable SKU / GTIN / MPN |
| Schema | Structured data where accurate |
| API discoverability | OpenAPI / well-known endpoints |
| Machine-readable policies | Terms / privacy structure |
| Service descriptions | Scope and constraints |
| Locations | Addresses, geo, hours |
| Booking information | Slots / reservation signals |
| Contact mechanisms | Hand-off channels |
| Returns | Return windows / conditions |
| Shipping | Methods, regions, ETA |
| Trust signals | Verifiable trust cues |

## Agent Readiness Score

Weighted composite (0–100) with bands: `nascent` · `emerging` · `operable` · `agent_ready`.

### Important product constraints

- **Separate from SEO / AEO / GEO** — measures machine-operability, not rankings or citation share.
- **Not a universal industry standard** — proprietary Peacock assessment; do not claim otherwise.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/agentic-readiness/catalog` | Checks, disclaimers, bands |
| `POST` | `/agentic-readiness/analyses` | Run assessment |
| `GET` | `/agentic-readiness/analyses/{id}` | Retrieve |

## Tables

`agentic_readiness_analyses`, `awr_check_results`, `awr_gaps`
