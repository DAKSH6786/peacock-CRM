# Dynamic model capability profiles

PINE routes work from **observed** model performance — not permanent role locks.

Do **not** hardcode forever:

- Claude = critic
- Perplexity = research
- GPT = strategy

Those may appear as **soft priors** when sample sizes are low. Observed
workspace profiles override them.

## Task types

| Code | Purpose |
| --- | --- |
| `RESEARCH` | Web / source research |
| `SEO_REASONING` | SEO analysis & recommendations |
| `GEO_REASONING` | Generative-engine visibility reasoning |
| `ENTITY_EXTRACTION` | Entity pulls |
| `CITATION_EXTRACTION` | Citation / source extraction |
| `STRUCTURED_OUTPUT` | Strict JSON / schema output |
| `CRITICAL_ANALYSIS` | Adversarial / critical review |
| `SUMMARISATION` | Compression / briefing |
| `STRATEGY` | Strategic synthesis |
| `CONTENT_ANALYSIS` | Content quality / gaps |
| `COMPETITOR_ANALYSIS` | Competitor comparison |
| `FACT_VERIFICATION` | Claim checking |
| `LONG_CONTEXT_ANALYSIS` | Large-context synthesis |

## Tracked metrics

| Metric | Meaning |
| --- | --- |
| `quality` | Task quality score 0–1 |
| `latency` | Average latency (ms) |
| `cost` | Average cost (USD micros) |
| `failure_rate` | Fraction of failed calls |
| `json_compliance` | Valid structured-output rate |
| `citation_accuracy` | Citation correctness 0–1 |
| `historical_agreement` | Agreement with prior trusted outcomes |

## Tables

| Table | Role |
| --- | --- |
| `model_capability_priors` | Soft global defaults (overridable) |
| `model_capability_profiles` | Workspace rolling aggregates |
| `model_capability_observations` | Per-invocation scored events |

## Routing

`CapabilityRouter.route(task_type=...)` scores candidates from blended
prior + observed metrics. Soft priors are discounted; sample-size trust
bonuses apply once enough observations exist. `permanent_role_locks` is
always `false`.

Bridge into the LLM gateway via `route_completion_request()` which sets
`request.provider` / `request.model`. Static `role_routing` on
`LLMGateway` is a **fallback only**.

## API

- `GET /capabilities/catalog`
- `POST /capabilities/priors/seed`
- `GET /capabilities/profiles`
- `POST /capabilities/observations`
- `POST /capabilities/route`

## Code

- ORM: `packages/db_models/capability_profiles.py`
- Service: `services/capability_router/`
- Migration: `infra/migrations/versions/0008_capability_profiles.py`
