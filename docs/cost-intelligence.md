# Peacock Cost Intelligence

**Intelligence Budget Engine** — because Peacock uses multiple models, searches, and repeated experiments, cost control is critical.

## Before deep workflows, estimate

| Field | Meaning |
| --- | --- |
| Expected calls | Model / tool invocations |
| Expected tokens | Prompt + completion tokens |
| Expected searches | Web / retrieval searches |
| Expected runtime | Wall-clock seconds |
| Expected cost | USD micros |

## Cheapest reliable method

PINE should choose the cheapest reliable method:

- Do **NOT** use five LLMs if deterministic data can answer the question.
- Do **NOT** run Council mode for a simple page-title recommendation.
- Reserve expensive reasoning for high-value decisions.

Complements Peacock mode hard envelopes (runtime enforcement) with **pre-flight** planning.

## Method ladder (cheap → expensive)

1. `deterministic` — rules, SQL, scores, graphs  
2. `web_search` — grounded search  
3. `single_llm` — one synthesis pass  
4. `multi_llm` — deep multi-agent  
5. `council` — adversarial debate  
6. `lab_experiment` — repeated measurements  

Decision value ceilings cap how far up the ladder a request may climb (`trivial` → deterministic only; `critical` may use lab).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/cost-intelligence/catalog` | Methods, values, profiles, policy |
| `GET` | `/cost-intelligence/preview` | Demo estimate (page-title → deterministic) |
| `POST` | `/cost-intelligence/estimates` | Persist a budget estimate |
| `GET` | `/cost-intelligence/estimates/{id}` | Retrieve estimate + candidates |

## Tables

`intelligence_budget_estimates`, `ibe_method_candidates`

## Related

- Peacock modes: `docs/peacock-modes.md` (hard `max_cost` / calls / runtime)
- Capability / ModelRouter: cost used as routing penalty; this engine plans *before* deep workflows
