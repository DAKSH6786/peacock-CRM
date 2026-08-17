# Evidence Ledger

Peacock One’s provenance spine. Every meaningful claim can optionally point
at evidence, and evidence participates in an explicit graph:

```text
Evidence → Finding → Recommendation → Action → Outcome
```

This is distinct from:

- `evidences` — lightweight explainability rows on decisions/recommendations
- `intelligence_case_evidence` — PINE case-scoped evidence slices

## Evidence types

| Type | Typical source |
| --- | --- |
| `CRAWL` | Peacock Crawler page/site facts |
| `SERP` | Search result snapshots |
| `ANALYTICS` | Traffic / engagement metrics |
| `SEARCH_CONSOLE` | GSC queries, clicks, impressions |
| `BACKLINK` | Referring domains / links |
| `AI_RESPONSE` | Generative engine answers / citations |
| `COMPETITOR_PAGE` | Competitor page observations |
| `USER_DATA` | First-party CRM / product signals |
| `MODEL_INFERENCE` | LLM-derived claims (tagged) |
| `EXTERNAL_SOURCE` | Third-party research connectors |
| `HISTORICAL_OUTCOME` | Prior measured outcomes |
| `EXPERIMENT` | A/B or controlled tests |

## Evidence fields

| Field | Storage |
| --- | --- |
| `source` | `ledger_evidences.source` |
| `timestamp` | `observed_at` |
| `freshness` | `freshness_hours` + `freshness_score` (0–1 decay) |
| `confidence` | `confidence` |
| `scope` | `scope_kind` + `scope_ref` |
| `supporting_value` | typed `value_text` / `value_number` / `value_bool` + `value_unit` |

No JSON blob for the supporting value.

## Graph tables

| Table | Role |
| --- | --- |
| `ledger_evidences` | Evidence nodes |
| `ledger_findings` | Finding / claim nodes |
| `ledger_recommendations` | Recommendation nodes (optional FK to central `recommendations`) |
| `ledger_actions` | Action nodes (optional roadmap / execution FKs) |
| `ledger_outcomes` | Outcome nodes (optional central outcome FK) |
| `ledger_evidence_finding_links` | Evidence → Finding |
| `ledger_finding_recommendation_links` | Finding → Recommendation |
| `ledger_recommendation_action_links` | Recommendation → Action |
| `ledger_action_outcome_links` | Action → Outcome |
| `ledger_claim_evidence_links` | Optional claim → evidence pointers from any domain |

## API

- `GET /evidence-ledger/types`
- `POST /evidence-ledger/evidences`
- `POST /evidence-ledger/findings`
- `POST /evidence-ledger/recommendations`
- `POST /evidence-ledger/actions`
- `POST /evidence-ledger/outcomes`
- `POST /evidence-ledger/claim-links`
- `GET /evidence-ledger/graph`
- `GET /evidence-ledger/trace/{evidence_id}`

## Code

- ORM: `packages/db_models/evidence_ledger.py`
- Types: `services/evidence_ledger/models.py`
- Repository: `services/evidence_ledger/repository.py`
- Migration: `infra/migrations/versions/0007_evidence_ledger.py`
