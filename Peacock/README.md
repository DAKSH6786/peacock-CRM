# Peacock One

Enterprise **SEO + AEO + GEO + AI Visibility growth platform**, built around the
flagship **Peacock Growth Loop**:

```text
SEO + AEO + GEO -> AI Visibility -> LLM Intelligence -> Opportunity Discovery
-> Content Strategy -> Content Creation -> Optimization -> AI Agents ->
Human Experts -> Publishing -> Measurement -> Experiments -> Learning ->
Re-optimization
```

The dashboard opens directly (no login required at this stage) at the
Peacock Command Centre, with the Growth Loop as the flagship module plus
dedicated modules for Website SEO/AEO/GEO Audit, Blog & Topic
Recommendations, Keyword & Backlink Recommendations, AI Visibility,
Content Optimizer, and Peacock GEO Intelligence.

## Repository layout

**`Peacock/`** is the **single project root** — every application file lives
inside it; nothing sits outside it except this repo's root-level pointer
files (`README.md`, `Makefile`, `.gitignore`, `.github/workflows/ci.yml`)
that just delegate into this folder.

Run the complete application from this folder:

```bash
cd Peacock
npm install
npm run dev
```

`npm install` installs the Next.js frontend **and** the Python API
environment. `npm run dev` starts both the FastAPI backend (`:8000`) and
the Next.js dashboard (`:3000`) together.

```text
Peacock/
├── frontend/                    # Next.js + React + TypeScript UI
├── backend/
│   ├── api/                     # FastAPI composition root (HTTP API) + growth_loop route
│   ├── main.py                   # ASGI entry re-export
│   ├── packages/                 # shared-types, scoring, db_models, job_runtime, observability, prompts, analytics
│   └── services/                 # growth_loop orchestrator + domain services not specific to one engine (auth, jobs, evidence ledger, council, judge, …)
├── plugins/                      # AI connectors — independent, common-interface LLM plugins
│   ├── openai/                    # ChatGPT
│   ├── gemini/                    # Gemini
│   ├── claude/                    # Claude (Anthropic)
│   ├── perplexity/                 # Perplexity
│   ├── deepseek/                   # DeepSeek
│   └── llm_gateway/                # Shared plugin contract + Peacock AI Gateway (ports, registry, factory)
├── engines/                       # SEO / AEO / GEO / crawler / AI-visibility / intelligence engines
│   ├── seo/                        # seo_engine, opportunity_engine (keyword/backlink ranking)
│   ├── aeo/                        # aeo_engine
│   ├── geo/                        # geo_engine, geo_lab, geo_intelligence, site_intelligence (enterprise SEO+GEO report)
│   ├── crawler/                    # Peacock Crawler (httpx + BeautifulSoup + Playwright, SSRF-protected)
│   ├── competitor-intelligence/     # deep_competitor, entity_intelligence, citation_graph, retrieval_pathway
│   ├── llm-intelligence/            # capability_router, share_of_answer, prompt_universe
│   ├── ai-visibility/               # AI Visibility Command Center (multi-platform brand/competitor/citation signals)
│   ├── citation-intelligence/       # Citation Gap Engine (real-fetches cited pages, diffs vs. your site)
│   ├── content-intelligence/        # Content Strategy Engine, Content Creation Studio, Multi-LLM Content Simulator
│   ├── opportunity-engine/          # peacock_opportunity — standalone Peacock Impact Score + TOP ACTIONS TO TAKE
│   ├── measurement/                 # Measurement Engine, Content Decay Detector, Competitor Change Radar
│   ├── experiment-engine/           # Structured SEO/GEO experiments (hypothesis -> baseline -> comparison)
│   └── learning-engine/             # peacock_learning — recommendation -> outcome ledger, confidence adjustment
├── agents/                        # peacock_agents — 12 modular AI agents (SEO, AEO, GEO, Research, Content
│                                   #   Strategist, Competitor, Citation, Internal Linking, Technical SEO,
│                                   #   Content Refresh, Measurement, Experiment). Analyse/recommend/draft only —
│                                   #   never publish, delete, or modify production without human approval.
├── experts/                       # peacock_experts — human review/approval workflow (AI Generated -> Human
│                                   #   Assigned -> Review -> Changes Requested -> Revised -> Approved -> Ready
│                                   #   to Publish), with assignee/comments/versions/review notes/approval.
├── publishing/                    # peacock_publishing — Publishing Connector interface: manual/draft (default,
│                                   #   safe), WordPress (real REST API, drafts only), Webflow/Shopify (stubs).
│                                   #   Publishing always requires explicit approval.
├── database/
│   └── migrations/                 # Alembic migrations
├── reports/                        # Generated SEO + GEO report output (gitignored)
├── tests/                          # Backend pytest suite (api/, services/)
├── scripts/                        # migrate_and_seed.sh, seed_dev.py
├── public/                         # Repo-wide static assets (frontend's own assets live in frontend/public)
├── docs/
├── terranova/
├── docker/                         # Dockerfiles (api, web, worker)
├── docker-compose.yml
├── package.json                 # npm install / npm run dev entry (orchestrates frontend + API)
├── pyproject.toml
├── .env.example
└── README.md (this file)
```

All SEO/AEO/GEO/AI-visibility/intelligence engines live under `engines/`;
all AI connectors/plugins live under `plugins/`; agents, human experts, and
publishing connectors each have their own top-level folder. Every package
keeps its original Python import name (e.g. `seo_engine`, `crawler`,
`llm_gateway`, `ai_visibility`, `peacock_agents`) — only its folder location
changed — so cross-engine imports work unchanged; see **PYTHONPATH** below.

> Two packages were deliberately renamed to avoid colliding with
> pre-existing `backend/services/` stubs of the same name: the new
> Learning Engine's importable package is `peacock_learning` (folder:
> `engines/learning-engine/`), and the new standalone Opportunity Engine's
> importable package is `peacock_opportunity` (folder:
> `engines/opportunity-engine/`), distinct from the pre-existing keyword/
> backlink `opportunity_engine` in `engines/seo/`.

## The Peacock Growth Loop

`POST /growth-loop/run` (frontend: **Peacock Growth Loop**, the first
section on both the Command Centre and the OS hub) runs the full flagship
workflow against a real URL in one call:

1. **SEO + AEO + GEO Intelligence** — `site_intelligence` (real crawl).
2. **AI Visibility Command Center** — `ai_visibility` broadcasts intent-varied
   queries to every configured AI plugin and reports mentions, competitor
   mentions, recommendation position, citations, attributes, sentiment,
   share of answer, and AI share of voice per platform.
3. **LLM Intelligence Extraction + Citation Gap Engine** — `citation_intelligence`
   real-fetches every URL an AI platform actually cited and diffs it
   against your own crawled content.
4. **Peacock Opportunity Engine** — `peacock_opportunity` ranks TOP ACTIONS
   TO TAKE by the Peacock Impact Score (`Visibility Opportunity x Business
   Relevance x Competitive Gap x Confidence / Implementation Difficulty`).
5. **Content Strategy Engine** — `content_intelligence` builds the
   Brand -> Topic -> Subtopic -> Entity -> Keyword -> Search Query -> AI
   Prompt -> Content Page relationship graph and recommends content types.
6. **Content Creation Studio ("CREATE WITH PEACOCK")** — a brief (research
   notes, outline, draft skeleton, sources needed, FAQs, metadata, schema,
   internal links, CTA, optimization checklist). Never fabricates research,
   statistics, quotations, citations, or sources.
7. **Multi-LLM Content Simulator + Optimizer** — deterministic GEO-score
   readiness plus, when a plugin is configured, a live critique.
8. **AI Agents** — 12 agents in `agents/` analyse everything above and
   prepare findings/recommendations/tasks/drafts. Read-only by construction.
9. **Human Experts** — a review task is created in `experts/` for the top
   content brief (AI Generated -> ... -> Ready to Publish).
10. **Publishing (preview)** — `publishing/`'s manual connector previews the
    content; nothing is ever auto-published (`published` is always `false`
    unless a human approves and a real CMS connector is separately
    configured and confirmed).
11. **Measurement** — a real snapshot of this run's Peacock-computed scores
    is captured for a future before/after comparison. Rankings,
    impressions, clicks, CTR, traffic, leads, and conversions are always
    reported as `"Data unavailable — connector required"`.
12. **Experiments** — top opportunities are ready to be logged as
    structured experiments via `/growth-loop/experiments`.
13. **Learning** — the top recommendation is logged to the outcome ledger
    for future confidence adjustment (never claims correlation = causation).

## Stack

| Layer | Choice |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind, Recharts, TanStack Query, Zustand |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL + **pgvector** (no separate vector DB) |
| Jobs | Redis + Celery behind a `JobRunner` port (Temporal-ready) |
| Crawl toolkit | Playwright, BeautifulSoup, HTTPX |
| AI plugins | OpenAI (ChatGPT), Gemini, Claude, Perplexity, DeepSeek — enabled only via environment variables |
| Publishing | Manual/draft (default), WordPress REST API (real, drafts only), Webflow/Shopify (stubs) |

## Core engineering rules

- Provider-specific LLM code lives **only** in `plugins/*` adapters, behind the shared `LLMProvider` interface in `plugins/llm_gateway`.
- Every external system has an interface (port); implementations are adapters.
- No hardcoded API keys — environment variables only.
- Long-running work is backgrounded with **status tracking**.
- Structured logging, typed responses, retries, rate-limit handling, timeouts.
- AI **cost** and **token** tracking on every LLM call.
- Recommendations must be explainable: store evidence, scores, decision traces — see `engines/geo/site_intelligence` for the evidence-first `ScoreFactor` model, and `peacock_opportunity` for the Peacock Impact Score.
- Never fabricate a metric: if a data source (backlinks, search volume, rankings, traffic, Core Web Vitals field data, an AI plugin's API key) isn't configured, the UI/API says "Data unavailable" instead of inventing a value.
- No agent or Autopilot cycle ever publishes, deletes, or modifies a production system without an explicit human approval step.
- Do **not** store hidden/private chain-of-thought — only structured summaries.

## Quick start

```bash
cd Peacock
npm install
npm run dev
```

Open **http://localhost:3000/** — the dashboard (Peacock Command Centre) loads
directly, with no login. `npm run dev` starts the FastAPI API on port 8000
and the Next.js UI on port 3000; the UI proxies `/backend/*` to the API.

Docker (optional, for Postgres/Redis-backed routes):

```bash
cd Peacock
cp .env.example .env
docker compose up --build
```

Or from the repository root: `make up`.

Services:

| Service | URL |
| --- | --- |
| **Web UI (open this in the browser)** | http://localhost:3000/ |
| Peacock One OS hub | http://localhost:3000/os |
| **Peacock Growth Loop (flagship)** | http://localhost:3000/modules/growth-loop |
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
- Docker (Postgres + Redis) — **optional** for the dashboard, the Website
  SEO/AEO/GEO Audit module, and the Peacock Growth Loop, all of which run
  against a real crawl with no database.

Work inside **`Peacock/`** (paths below are relative to that folder):

```bash
cd Peacock
npm install    # installs frontend deps + Python API environment
npm run dev    # API on :8000 + Next.js on :3000

# Optional: enable full persistence-backed routes
docker compose up -d postgres redis
alembic -c database/migrations/alembic.ini upgrade head
python scripts/seed_dev.py

# Celery worker (separate terminal, optional)
source .venv/bin/activate
celery -A api.worker.celery_app worker --loglevel=INFO
```

Open http://localhost:3000 — it opens directly on the Peacock Command Centre
dashboard, with the Peacock Growth Loop as the first flagship section.

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

### Enabling a publishing connector

| Connector | Environment variables | Notes |
| --- | --- | --- |
| Manual (default) | none | Always available; never calls an external system — only marks content ready for manual publish. |
| WordPress | `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_APP_PASSWORD` | Real WP REST API integration; creates **drafts only**, even with `confirm=true`. |
| Webflow | `WEBFLOW_API_TOKEN`, `WEBFLOW_COLLECTION_ID` | Reports configuration status; CMS-item creation is a stub — extend `WebflowConnector.publish()`. |
| Shopify | `SHOPIFY_STORE_DOMAIN`, `SHOPIFY_ADMIN_API_TOKEN` | Reports configuration status; blog-article creation is a stub — extend `ShopifyConnector.publish()`. |

## Tests

```bash
cd Peacock
npm test
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
