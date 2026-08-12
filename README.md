# Peacock One

Enterprise **SEO + AEO + GEO Search & Generative Visibility Intelligence** platform.

Peacock One is **not** a thin LLM wrapper. Long-running intelligence work follows:

```text
OBSERVE → THINK → VERIFY → DECIDE → EXECUTE → MEASURE → LEARN
```

This repository is a **monorepo**. Business features are intentionally not implemented yet — this stage delivers runnable architecture only.

## Repository layout

```text
peacock-one/
├── apps/
│   ├── web/                 # Next.js + React + TypeScript UI
│   └── api/                 # FastAPI composition root (HTTP API)
├── services/                # Domain engines (Python packages; snake_case imports)
│   ├── crawler/
│   ├── intelligence/
│   ├── llm_gateway/         # Provider adapters ONLY — no business logic
│   ├── seo_engine/
│   ├── geo_engine/
│   ├── aeo_engine/
│   ├── content_engine/
│   ├── writer_engine/
│   ├── competitor_engine/
│   ├── strategy_engine/
│   ├── monitoring_engine/
│   └── learning_engine/
├── packages/
│   ├── shared-types/        # Cross-cutting TypeScript contracts
│   ├── scoring/             # Deterministic scoring helpers
│   ├── prompts/             # Prompt templates (role-bound, not provider-bound)
│   ├── analytics/           # Analytics event contracts
│   ├── db_models/           # SQLAlchemy models + multi-tenant base
│   ├── job_runtime/         # Celery now / Temporal-ready job ports
│   └── observability/       # Structured logging, cost/token/audit helpers
├── infra/
│   ├── docker/              # Dockerfiles
│   ├── migrations/          # Alembic
│   └── scripts/             # Dev/ops scripts
├── docs/
├── tests/
├── docker-compose.yml
└── pyproject.toml
```

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind, shadcn/ui, Recharts, TanStack Query, Zustand |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL + **pgvector** (no separate vector DB) |
| Jobs | Redis + Celery behind a `JobRunner` port (Temporal-ready) |
| Crawl toolkit | Playwright, BeautifulSoup, HTTPX (Scrapy only if needed later) |
| Auth | Users, organisations, workspaces, roles, permissions — email/password now; Google/Microsoft OAuth prepared |

## Core engineering rules

- Provider-specific LLM code lives **only** in `services/llm-gateway` adapters.
- Every external system has an interface (port); implementations are adapters.
- No hardcoded API keys — environment variables only.
- Long-running work is backgrounded with **status tracking**.
- Structured logging, typed responses, retries, rate-limit handling, timeouts.
- AI **cost** and **token** tracking on every LLM call.
- Audit logs for sensitive operations.
- Multi-tenant by default — organisation boundaries are enforced in queries.
- Recommendations must be explainable: store evidence, scores, decision traces.
- Do **not** store hidden/private chain-of-thought — only structured summaries.

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Services:

| Service | URL |
| --- | --- |
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |

Default local admin (seeded):

- Email: `admin@peacock.one`
- Password: `ChangeMeNow!123`

## Local development (without rebuilding images)

### Prerequisites

- Node.js 22+
- Python 3.12+
- Docker (Postgres + Redis)

```bash
# Infrastructure only
docker compose up -d postgres redis

# Python API
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic -c infra/migrations/alembic.ini upgrade head
python infra/scripts/seed_dev.py
uvicorn apps.api.main:app --reload --host 0.0.0.0 --port 8000

# Celery worker (separate terminal)
celery -A apps.api.worker.celery_app worker --loglevel=INFO

# Web
cd apps/web && npm install && npm run dev
```

## Tests

```bash
source .venv/bin/activate
pytest tests/ -q
cd apps/web && npm test
```

## Environments

| Env | File | Notes |
| --- | --- | --- |
| local | `.env` / `.env.example` | Docker Compose defaults |
| staging | `.env.staging.example` | Separate DB/Redis, stricter CORS |
| production | `.env.production.example` | Secrets from vault/CI; never commit |

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system design
- [`docs/multi-tenancy.md`](docs/multi-tenancy.md) — org/workspace isolation
- [`docs/jobs.md`](docs/jobs.md) — Celery → Temporal migration path
- [`docs/llm-gateway.md`](docs/llm-gateway.md) — adapter rules
- [`docs/auth.md`](docs/auth.md) — auth model & OAuth prep
