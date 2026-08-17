# Functional status (honest)

Last updated with migration tip **0041_final_architecture** and OS hub UI.

## Absolute product

Peacock One = Adaptive Search, Answer & Generative Intelligence Operating System — **not** “Semrush + an AI dashboard.”

## What is functional today

### Browser URLs (avoid 404 confusion)

| What you want | Correct URL |
| --- | --- |
| Product UI | `http://localhost:3000/` (Next.js) |
| API docs / health | `http://localhost:8000/docs` · `/health` |
| Frontend → API | same-origin `/backend/...` rewrite to FastAPI |

Port **8000** is API-only. Opening it as the UI used to show a bare FastAPI 404; `/` now returns a JSON pointer to the web UI.

### Product UI surfaces (live preview + demo fallback)

| Surface | Route | API | Notes |
| --- | --- | --- | --- |
| Command Centre | `/` | `/command-centre/preview` | Functional preview; demo snapshot if API down |
| Executive Brain | `/executive` | `/executive-brain/preview` | Same pattern |
| Research Mode | `/research` | `/research-mode/preview` | Laboratory UI |
| Proprietary Metrics | `/metrics` | `/proprietary-metrics/preview` | Documented formulas UI |
| Platform ops | `/ops` | health/crawl/SEO | Ops tools |
| **Peacock One OS hub** | `/os` | `/final-architecture/preview` + subsystem links | Architecture + product standard |
| Final Architecture | `/architecture` | `/final-architecture/preview` | System map UI |
| Quality Bar | `/quality` | `/quality-bar/preview` | Completeness gates UI |
| Cost Intelligence | `/cost` | `/cost-intelligence/preview` | Budget engine UI |
| Moat Data Model | `/moat` | `/moat-data-model/preview` | Pathway preview UI |
| Enterprise Reliability | `/reliability` | `/enterprise-reliability/preview` | Partial-results preview UI |
| AI Connector Security | `/security` | `/ai-connector-security/preview` | Untrusted I/O preview UI |

### Backend vertical slices 0036–0041

Each has: ORM + Alembic + domain engine + service + API (`/catalog`, `/preview`, authenticated create/get) + pytest.

| Module | Migration | Functional for | Not yet |
| --- | --- | --- | --- |
| Moat Data Model | 0036 | Demo pathway accumulation + optional persist | Live ingest from all domain SORs |
| Cost Intelligence | 0037 | Pre-flight method/cost estimates | Live gateway metering / hard enforcement on every call |
| Enterprise Reliability | 0038 | Simulated partial provider reports + control records | Live circuit breakers on real LLM calls |
| AI Connector Security | 0039 | Heuristic injection/PII/URL/permission scans | Gateway middleware on every connector call |
| Quality Bar | 0040 | Gate assessment from catalog/answers | Auto-introspection of every module |
| Final Architecture | 0041 | System map + product-question coverage | Dynamic runtime topology discovery |

These engines are **deterministic domain logic** (no mock “fake success” without running the engine). Persistence to Postgres works when `DATABASE_URL` is configured and migrations applied. They are **not** claimed as live multi-provider production control planes until wired through `llm_gateway` / `job_runtime`.

## External credentials required

| Capability | Credentials |
| --- | --- |
| Preview/catalog/persist domain engines 0036–0041 | **None** (deterministic) |
| Live LLM completions (PINE fabric) | Provider API keys via LLM gateway adapters |
| Live web crawl of third-party sites | Network egress; respect robots/ToS |
| Celery workers | Redis/broker as configured |
| Auth-protected POST create routes | Valid JWT / org-workspace membership |

## Async processing

Job runtime ports exist (`packages/job_runtime`). Features 0036–0041 run **synchronously** on request today. Long-running multi-provider measurement should use jobs when wired for production.

## Build verification checklist

Follow [`cursor-execution-rule.md`](./cursor-execution-rule.md):

```bash
JOB_BACKEND=memory PYTHONPATH=.:apps/api:services:packages \
  python3 -m pytest tests/services/test_moat_data_model.py \
  tests/services/test_cost_intelligence.py \
  tests/services/test_enterprise_reliability.py \
  tests/services/test_ai_connector_security.py \
  tests/services/test_quality_bar.py \
  tests/services/test_final_architecture.py \
  tests/services/test_schema_integrity.py -q

cd apps/web && npm test && npm run lint && npm run typecheck
```

### Verified on this branch

| Check | Result |
| --- | --- |
| Backend pytest (0036–0041 + schema) | Passed (skipped only when Postgres unavailable) |
| Web vitest | Passed |
| Web typecheck (`tsc --noEmit`) | Passed |
| Web lint (`eslint src/**/*.{ts,tsx}`) | Passed |

`next lint` is deprecated / broken with current ESLint 9 + `eslint-config-next` circular config in this environment; the web `lint` script uses the ESLint CLI flat config instead.
