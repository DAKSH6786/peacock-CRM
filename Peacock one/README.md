# Peacock One

Enterprise **SEO + AEO + GEO Search & Generative Visibility Intelligence** platform.

Peacock One is **not** a thin LLM wrapper. Its workflow follows:

```text
Crawl → Understand → Benchmark → Query LLMs → Extract AI Signals →
Compare Competitors → Identify Gaps → Prioritize Opportunities →
Generate Exact Fixes → Track Improvement
```

The dashboard opens directly (no login required in this stage) at the
Peacock Command Centre, with dedicated modules for Website SEO/AEO/GEO
Audit, Blog & Topic Recommendations, Keyword & Backlink Recommendations,
AI Visibility, Content Optimizer, and Peacock GEO Intelligence.

## Repository layout

`peacock-one/` is the **single project root** — everything lives inside it:

```text
peacock-one/
├── frontend/                 # Next.js + React + TypeScript UI
├── backend/
│   ├── api/                  # FastAPI composition root (HTTP API)
│   ├── main.py                # ASGI entry re-export
│   ├── packages/              # shared-types, scoring, db_models, job_runtime, observability, prompts, analytics
│   └── services/              # Domain services not specific to SEO/AEO/GEO/crawler/competitor/LLM (auth, jobs, evidence ledger, council, judge, …)
├── plugins/                   # AI connectors — independent, common-interface LLM plugins
│   ├── openai/                 # ChatGPT
│   ├── gemini/                 # Gemini
│   ├── claude/                 # Claude (Anthropic)
│   ├── perplexity/              # Perplexity
│   ├── deepseek/                # DeepSeek
│   └── llm_gateway/             # Shared plugin contract + Peacock AI Gateway (ports, registry, factory)
├── engines/                    # SEO / AEO / GEO / crawler / competitor / LLM intelligence engines
│   ├── seo/                     # seo_engine, opportunity_engine
│   ├── aeo/                     # aeo_engine
│   ├── geo/                     # geo_engine, geo_lab, geo_intelligence, site_intelligence (enterprise SEO+GEO report)
│   ├── crawler/                 # Peacock Crawler (httpx + BeautifulSoup + Playwright, SSRF-protected)
│   ├── competitor-intelligence/ # deep_competitor, entity_intelligence, citation_graph, retrieval_pathway
│   └── llm-intelligence/        # capability_router, share_of_answer, prompt_universe
├── database/
│   └── migrations/              # Alembic migrations
├── reports/                     # Generated SEO + GEO report output (gitignored)
├── tests/                       # Backend pytest suite (api/, services/)
├── scripts/                     # migrate_and_seed.sh, seed_dev.py
├── public/                      # Repo-wide static assets (frontend's own assets live in frontend/public)
├── docs/
├── terranova/
├── docker/                      # Dockerfiles (api, web, worker)
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md (this file)
```

All SEO/AEO/GEO engines live under `engines/`; all AI connectors/plugins live
under `plugins/`. Every package keeps its original Python import name (e.g.
`seo_engine`, `crawler`, `llm_gateway`) — only its folder location changed —
so cross-engine imports work unchanged; see **PYTHONPATH** below.

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind, Recharts, TanStack Query, Zustand |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL + **pgvector** (no separate vector DB) |
| Jobs | Redis + Celery behind a `JobRunner` port (Temporal-ready) |
| Crawl toolkit | Playwright, BeautifulSoup, HTTPX |
| AI plugins | OpenAI (ChatGPT), Gemini, Claude, Perplexity, DeepSeek — enabled only via environment variables |

## Core engineering rules

- Provider-specific LLM code lives **only** in `plugins/*` adapters, behind the shared `LLMProvider` interface in `plugins/llm_gateway`.
- Every external system has an interface (port); implementations are adapters.
- No hardcoded API keys — environment variables only.
- Long-running work is backgrounded with **status tracking**.
- Structured logging, typed responses, retries, rate-limit handling, timeouts.
- AI **cost** and **token** tracking on every LLM call.
- Recommendations must be explainable: store evidence, scores, decision traces — see `engines/geo/site_intelligence` for the evidence-first `ScoreFactor` model.
- Never fabricate a metric: if a data source (backlinks, search volume, Core Web Vitals field data, an AI plugin's API key) isn't configured, the UI/API says "Data unavailable" instead of inventing a value.
- Do **not** store hidden/private chain-of-thought — only structured summaries.

## Quick start (Docker)

```bash
cd peacock-one
cp .env.example .env
docker compose up --build
```

Or from the repository root: `make up`.

Services:

| Service | URL |
| --- | --- |
| **Web UI (open this in the browser)** | http://localhost:3000/ |
| Peacock One OS hub | http://localhost:3000/os |
| Website SEO/AEO/GEO Audit (real crawl analyzer) | http://localhost:3000/modules/seo-audit |
| Peacock GEO Intelligence | http://localhost:3000/modules/geo-intelligence |
| Platform ops | http://localhost:3000/ops |
| API (JSON only — not the UI) | http://localhost:8000/ |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |

The frontend calls the API through the same-origin `/backend/*` rewrite (see
`frontend/next.config.ts`). Do not open port `8000` expecting product pages.

Default local admin (seeded, only relevant once auth is re-enabled):

- Email: `admin@peacock.one`
- Password: `ChangeMeNow!123`

## Local development (without rebuilding images)

### Prerequisites

- Node.js 22+
- Python 3.12+
- Docker (Postgres + Redis) — **optional** for the dashboard and Website
  SEO/AEO/GEO Audit module, which run against a real crawl with no database.

Work inside **`peacock-one/`** (paths below are relative to that folder):

```bash
cd peacock-one

# PYTHONPATH covers backend + every engines/*  and plugins/ directory
export PYTHONPATH=".:backend:backend/packages:backend/services:engines/seo:engines/aeo:engines/geo:engines/crawler:engines/competitor-intelligence:engines/llm-intelligence:plugins"

# Python API — Postgres/Redis are only required for auth/crawl-persistence/job routes
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Optional: enable full persistence-backed routes
docker compose up -d postgres redis
alembic -c database/migrations/alembic.ini upgrade head
python scripts/seed_dev.py

# Celery worker (separate terminal, optional)
celery -A api.worker.celery_app worker --loglevel=INFO

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

Open http://localhost:3000 — it opens directly on the Peacock Command Centre
dashboard.

### Enabling an AI plugin

Each plugin activates automatically once its API key is set as an
environment variable — no code changes required:

| Plugin | Environment variable |
| --- | --- |
| ChatGPT (OpenAI) | `OPENAI_API_KEY` |
| Gemini | `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) |
| Claude (Anthropic) | `ANTHROPIC_API_KEY` |
| Perplexity | `PERPLEXITY_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |

## Tests

```bash
cd peacock-one
source .venv/bin/activate
export PYTHONPATH=".:backend:backend/packages:backend/services:engines/seo:engines/aeo:engines/geo:engines/crawler:engines/competitor-intelligence:engines/llm-intelligence:plugins"
JOB_BACKEND=memory pytest tests/ -q
cd frontend && npm test
```

## Environments

| Env | File | Notes |
| --- | --- | --- |
| local | `.env` / `.env.example` | Docker Compose defaults |
| staging | `.env.staging.example` | Separate DB/Redis, stricter CORS |
| production | `.env.production.example` | Secrets from vault/CI; never commit |

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system design
- [`docs/erd.md`](docs/erd.md) — ERD, cascade rules, JSONB policy
- [`docs/multi-tenancy.md`](docs/multi-tenancy.md) — org/workspace isolation
- [`docs/jobs.md`](docs/jobs.md) — Celery → Temporal migration path
- [`docs/llm-gateway.md`](docs/llm-gateway.md) — plugin/adapter rules
- [`docs/auth.md`](docs/auth.md) — auth model & OAuth prep (currently disabled at the UI layer)
