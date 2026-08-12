# Strategic Intelligence — Layers 0–10

Every sufficiently complex strategic request is decomposed into conceptual layers.

## Layers

| Layer | Name | Responsibility |
| --- | --- | --- |
| 0 | Request Classification | intent, output, importance, business risk, freshness, required data, thinking depth |
| 1 | Context Assembly | intelligent selection of organisation context — **never a full DB dump** |
| 2 | Deterministic Evidence | quantitative crawl/SEO/visibility/performance facts |
| 3 | Research | fresh external evidence via specialised connectors |
| 4 | Specialist Reasoning | specialised agents (deterministic + LLM-tagged) |
| 5 | Adversarial Analysis | challenge unsupported claims |
| 6 | Verification | consistency / consensus checks |
| 7 | Decision | ranked recommendations |
| 8 | Simulation | consequences and alternatives |
| 9 | Execution Plan | tasks with owners and success metrics |
| 10 | Learning | outcome hooks for future weight updates |

## Guarantees

1. **Intelligent context selection** — relevance + token budget + max items; rejected kinds are explicit.
2. **Deterministic evidence ≠ LLM inference** — stored in separate bundles (`deterministic`, `research`, `inferences`).
3. **Numeric ranking** uses deterministic `weighted_score(impact, confidence, effort)`.

## API

- `POST /intelligence/runs`
- `GET /intelligence/runs/{id}`
- `GET /intelligence/layers`

## Code

- `services/intelligence/pipeline.py`
- `services/intelligence/layers.py`
- `services/intelligence/context_selector.py`
- `services/intelligence/evidence.py`
