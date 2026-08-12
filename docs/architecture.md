# System architecture

## Composition

```text
apps/web  ──HTTP──►  apps/api (FastAPI)
                        │
                        ├── services/* domain engines
                        ├── services/llm_gateway (adapters only)
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

## Cognitive loop (future features)

OBSERVE → THINK → VERIFY → DECIDE → EXECUTE → MEASURE → LEARN

This stage only scaffolds orchestrator/engine packages.
