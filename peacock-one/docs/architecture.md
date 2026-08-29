# System architecture

## Composition

Paths below are relative to the monorepo root **`Peacock/`**.

```text
frontend  ──HTTP──►  backend/api (FastAPI)
                        │
                        ├── services/* domain engines
                        ├── plugins/llm_gateway (adapters only)
                        ├── packages/db_models + Alembic
                        └── packages/job_runtime → Celery (Temporal-ready)
```

## Rules enforced by structure

1. **No provider SDKs in business services** — only `llm_gateway` adapters talk to OpenAI/Anthropic/Gemini/Perplexity/DeepSeek.
2. **Ports over concretions** — crawlers, jobs, LLM, audit sinks are interfaces.
3. **Multi-tenant by default** — `organisation_id` on tenant-owned tables; auth context validates workspace ownership.
4. **Long-running = jobs** — enqueue via `JobRunner`, persist `background_jobs` status.
5. **Explainability** — recommendations later must store evidence + scores + decision traces; never private CoT.
6. **Embeddings in Postgres** — `pgvector` on `embedding_chunks`.
7. **Relational modelling first** — see [`docs/erd.md`](./erd.md) for FKs, cascades, and JSONB policy.

## Cognitive loop

See **Final Peacock Architecture**: [`docs/final-architecture.md`](./final-architecture.md)

```text
OBSERVE → EVIDENCE → PINE → COUNCIL → CRITIC → VERIFY → JUDGE
  → SIMULATE → RECOMMEND → ACT → EXECUTE → MONITOR → EXPERIMENT
  → OUTCOMES → LEARN → PINE
```

Product standard: not only “How visible are we?” — certainty, why, competitors,
sources, entities, intents, change, EV, ownership, inaction, outcomes, learning.

**Absolute product:** [`docs/peacock-one-os.md`](./peacock-one-os.md) —
Adaptive Search, Answer & Generative Intelligence Operating System (not Semrush + AI dashboard).

**Execution discipline:** [`docs/cursor-execution-rule.md`](./cursor-execution-rule.md) ·
honest status: [`docs/functional-status.md`](./functional-status.md).
