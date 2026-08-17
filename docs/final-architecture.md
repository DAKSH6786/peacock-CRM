# Final Peacock Architecture

The completed system conceptually becomes:

```text
                         PEACOCK ONE
                              │
                              ▼
                     DATA OBSERVATION LAYER
        ┌────────────┬──────────────┬──────────────┐
        │            │              │              │
      Website      Search          AI         Competitors
        │            │              │              │
        ├──────── Analytics         │              │
        │            │              │              │
        └────────────┴──────────────┴──────────────┘
                              │
                              ▼
                       EVIDENCE LEDGER
                              │
                              ▼
                             PINE
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
      SPECIALISTS        LLM FABRIC         DATA MODELS
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                     PEACOCK COUNCIL
                              ▼
                         CRITIC LAYER
                              ▼
                     VERIFICATION LAYER
                              ▼
                       PEACOCK JUDGE
                              ▼
                 COUNTERFACTUAL SIMULATION
                              ▼
                    RECOMMENDATION ENGINE
                              ▼
                      PEACOCK ACTION ENGINE
                              ▼
                          EXECUTION
                              ▼
                         MONITORING
                              ▼
                         EXPERIMENTS
                              ▼
                     OUTCOME MEASUREMENT
                              ▼
                     PEACOCK LEARNING
                              │
                              └──────────────► PINE
```

## The fundamental product difference

Do **not** build Peacock One to answer only:

> How visible are we?

Build it to answer:

1. How visible are we?
2. How certain are we?
3. Why?
4. Compared with whom?
5. Which sources are causing it?
6. Which entities are influencing it?
7. Which customer intents are we losing?
8. What should we change?
9. Which action has the highest expected value?
10. Who should execute it?
11. What happens if we don't?
12. Did the change work?
13. What did Peacock learn?

**That is the standard for Peacock One.**

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/final-architecture/catalog` | Stages, sources, PINE lanes, product questions |
| `GET` | `/final-architecture/preview` | Full architecture map demo |
| `POST` | `/final-architecture/maps` | Persist a map snapshot |
| `GET` | `/final-architecture/maps/{id}` | Retrieve map |

## Tables

`final_architecture_maps`, `fa_pipeline_stages`, `fa_observation_sources`, `fa_pine_lanes`, `fa_product_questions`

## Related

- Monorepo composition: [`architecture.md`](./architecture.md)
- Quality Bar: [`quality-bar.md`](./quality-bar.md)
- Learning loop: [`learning-engine2.md`](./learning-engine2.md)
