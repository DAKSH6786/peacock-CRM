# Peacock One — Final End-to-End Audit

**Branch:** `cursor/peacock-final-audit-5408`  
**Audit date:** 2026-08-17  
**Migration tip:** `0041_final_architecture`  
**Method:** Code inspection + live Postgres/Redis + Alembic migrate/seed + API probes + full pytest + web lint/typecheck/build. Critical/high defects fixed and retested.

---

## Overall backend readiness

| Metric | Value |
| --- | --- |
| **Backend readiness score** | **62 / 100** |
| **Production readiness** | **CONDITIONAL** |

**Why not READY:** Live LLM adapters are scaffolded (`NotImplementedError`); the API registers only `NullLLMProvider`; AI visibility / GEO probes are deterministic mocks; AEO and monitoring v1 are scaffolds; RBAC helpers exist but are not enforced on routes; several product surfaces silently fill demo data when inputs are empty.

**Why not NOT READY:** Postgres schema through 0041 applies cleanly; crawler→SEO→PINE→Council/Judge/Writer/Content/Peacock90/Learning2/Ask/Evidence ledger execute real deterministic engines; health/ready report DB+Redis correctly after this audit; 226 backend tests and web production build pass.

---

## Module PASS / FAIL

| Module | Status | Real vs Mock / Placeholder |
| --- | --- | --- |
| Backend (FastAPI wiring, health) | **PASS** | Real process; LLM = Null only |
| Database (models + migrations) | **PASS** | Real Alembic 0001–0041 + seed |
| Crawler | **PASS** | Real crawl; SSRF protection added this audit |
| SEO | **PASS** | Deterministic analyzers; connectors **mock by default** |
| AEO | **FAIL** | Scaffold only (`ready=False`, no engine routes) |
| GEO | **FAIL** | Orchestration real; **live engine probes not enabled** |
| AI Visibility | **FAIL** | Distributional scoring real; probes = `mock_deterministic` |
| Multi-LLM Gateway | **PARTIAL** | Registry/retry/timeout real; 5 live adapters **NOT LIVE** |
| PINE | **PASS** | Layers 0–10 deterministic; demo context/research when empty |
| Peacock Council (Council2) | **PASS** | Real opposing-role debate (template/heuristic, not live multi-LLM) |
| Peacock Judge (Judge2) | **PASS** | Deterministic multi-signal scoring outside LLM |
| Competitor Intelligence | **PASS** | Deep Competitor formulas real (needs caller-supplied candidates); legacy scaffold superseded |
| Content Intelligence | **PASS** | Content Lab deterministic; legacy scaffold superseded |
| Writer Intelligence | **PASS** | Writer DNA + history scoring (no hardcoded writer IDs) |
| Peacock 90 | **PASS** | Capacity-constrained optimiser; may fill default candidates if empty |
| Monitoring | **FAIL** | Scaffold only; no monitoring API routes / no v2 |
| Learning Engine | **PASS** | Learning Engine 2.0 records/aggregates outcomes (v1 scaffold superseded) |
| Ask Peacock | **PASS** | Structured answers; **silent `demo_graph_signals` if empty** |
| Security | **FAIL** | SSRF + ACS heuristics fixed/present; **RBAC not enforced** |
| Tests | **PASS** | **226 passed / 0 failed** |
| Production Build (Next.js) | **PASS** | `npm run build` succeeded |

---

## External APIs

| Provider | Adapter status | Live verified this audit |
| --- | --- | --- |
| OpenAI | Scaffold raises `NotImplementedError` after key check | **IMPLEMENTED BUT NOT LIVE VERIFIED** |
| Anthropic (Claude) | Same | **IMPLEMENTED BUT NOT LIVE VERIFIED** |
| Gemini | Same | **IMPLEMENTED BUT NOT LIVE VERIFIED** |
| Perplexity | Same | **IMPLEMENTED BUT NOT LIVE VERIFIED** |
| DeepSeek | Same | **IMPLEMENTED BUT NOT LIVE VERIFIED** |
| Null provider | Wired in `create_app` | Verified (only provider registered) |

No provider API credentials were available in this environment. Successful live completions were **not** claimed.

Gateway routing/fallback/retry/timeout/cost shells exist around the registry; they cannot be live-verified without working adapters.

---

## Infrastructure verification (this run)

| Check | Result |
| --- | --- |
| PostgreSQL 16 + `vector` extension | Started; `peacock_one` migrated to head |
| Redis | `PONG`; `/health` redis=`ok` |
| Alembic `upgrade head` | PASS (0041) |
| Seed (`infra/scripts/seed_dev.py`) | PASS |
| `/health` | `status=ok`, database/redis ok, `job_backend=memory` |
| `/ready` | `ready=true`, `database=true`, `redis=true`, `llm_live_adapters=false`, `llm_provider=null` |
| Celery workers | Not required for memory backend; Temporal runner remains `NotImplementedError` |
| Docker Compose | Not available in this VM (Postgres/Redis installed directly) |

---

## Functional flow probed

```text
Website → Crawl → SEO Audit → (AEO scaffold) → GEO/Visibility (mock probes)
→ Competitor (Deep) → Content Lab → Writer Intelligence → PINE
→ Multi-LLM Gateway (Null only) → Council2 → Judge2 → Peacock 90
→ Monitoring (absent) → Learning2 → Ask Peacock
```

| Step | Live probe result |
| --- | --- |
| Website ingest | PASS (`POST /websites`) |
| Crawl `example.com` | PASS (completed) |
| SSRF `127.0.0.1` / link-local metadata | PASS (HTTP 400 blocked) |
| SEO audit | PASS (deterministic score; PageSpeed input marked `source=mock_pagespeed`) |
| AEO | FAIL — no routes |
| Visibility campaign + run | PASS engine; `probe_mode=mock_deterministic` |
| Deep Competitor create | PASS |
| Content Lab create | PASS |
| Writer Intelligence create | PASS (DNA/history based) |
| PINE `/intelligence/runs` | PASS (`peacock_standard`, layers completed) |
| Council2 / Judge2 / Peacock90 | PASS |
| Learning2 run | PASS |
| Ask Peacock session | PASS |
| Evidence → Finding → Recommendation → Action → Outcome | PASS (ledger APIs) |
| Org-scoped 404 on foreign campaign score | PASS (tenant miss) |

---

## Issues found

### Critical (fixed this audit)

1. **`/services/status` crashed** — `CrawlerService` used `@dataclass(slots=True)` without declaring `_store`/`_engine` fields → `AttributeError`. **Fixed.**
2. **Visibility dead branch** — `probe_fn = mock if use_mock else mock` could label observations `live` falsely. **Fixed:** `use_mock=False` raises; score cards expose `probe_mode`.
3. **Crawler SSRF gap** — localhost/private/metadata hosts allowed. **Fixed:** `assert_public_crawl_target` in engine + API `/crawls` and `/websites`; `allow_private_hosts` opt-in for tests only.

### High (fixed or honesty-corrected)

4. Scaffolds advertised `ready: True` with `features_implemented: False` (AEO, monitoring, learning v1, competitor/content/writer/strategy). **Fixed:** `ready=False`.
5. GEO/SEO status overclaimed live I/O. **Fixed:** disclose `probe_mode` / `live_connectors=False`.
6. `/ready` ignored Redis and implied full readiness. **Fixed:** requires Redis; declares `llm_live_adapters=false`.
7. Invalid `peacock_mode` caused HTTP 500. **Fixed:** clear `ValueError` → HTTP 400.

### Medium (open)

8. Live LLM adapters not implemented; app never registers them.
9. `require_roles` / Permission tables unused — RBAC not enforced beyond org membership JWT.
10. Silent demo fills: Ask Peacock, Peacock90 empty candidates, Deep Competitor default dimension scores, many UI `DEMO_*` fallbacks.
11. SEO external connectors mock-by-default (disclosed).
12. Share-of-Answer extractor is hash-seeded mock prominence.
13. Council2 is template debate, not multi-provider LLM council.
14. ACS `secrets_exposure_blocked` is fail-closed always-true (policy stance, weak signal fidelity).
15. Evidence lineage optional — recommenders do not auto-write ledger links.

### Low (open)

16. Temporal job backend reserved (`NotImplementedError`).
17. Legacy engine names still listed on `/services/status` beside real superseding modules.
18. Frontend demo fallbacks can hide API failures in product UI.

---

## Security

| Control | Status |
| --- | --- |
| Crawler SSRF (private IP, localhost, metadata, DNS→private) | **PASS** (added) |
| AI Connector Security heuristics (injection/PII/URL/scopes) | **PARTIAL** — real engine; not gateway middleware |
| Prompt-injection resistance on live LLM path | **N/A / FAIL** — Null provider only; no live completions |
| Secret protection | **PARTIAL** — ACS fail-closed; crawler bodies treated as DATA in ACS |
| Input validation | **PASS** on audited create schemas |
| Tenant isolation (org_id on reads/writes) | **PASS** for probed routes |
| RBAC role enforcement | **FAIL** — `require_roles` unused |

**Security verdict for summary table: FAIL** (RBAC gap + no live LLM safety path).

---

## Performance bottlenecks

1. Inline crawls/audits/PINE on request thread (fine for lab; not for large sites).
2. Visibility mock loops are rate-limited artificially — live probe volume will need job workers + Redis Celery.
3. Council/Judge/Ask can return large JSON payloads (evidence-heavy Ask sessions).
4. No observed query N+1 crisis in this audit, but evidence graph growth needs indexing discipline in production.

---

## Top 5 remaining risks

1. **Shipping mock visibility / null LLM as “AI visibility product”** — scores look real (`probe_mode` must stay visible).
2. **Enabling live adapters without SSRF/ACS middleware on every connector call.**
3. **RBAC gap** — any authenticated org member can hit privileged routes.
4. **Demo-fill UX** — empty Ask/Command Centre can look like production telemetry.
5. **AEO + Monitoring product claims** — schema/status history without engines.

---

## Fixes shipped on this branch

- Crawler SSRF helpers + policy `allow_private_hosts` + API boundary checks  
- `CrawlerService` slots field fix for `/services/status`  
- Visibility live-probe refusal + `probe_mode` on score cards  
- Honest `ready` / mock-disclosure on scaffold and GEO/SEO/PINE status  
- `/ready` Redis + LLM honesty fields  
- Invalid Peacock mode → 400  
- Regression tests: `tests/services/test_audit_honesty_and_ssrf.py`

---

## Test / build matrix (post-fix)

| Suite | Result |
| --- | --- |
| `pytest tests/` | **226 passed / 0 failed** |
| `apps/web` vitest | 11 passed |
| `npm run lint` | PASS |
| `npm run typecheck` | PASS |
| `npm run build` | PASS |

---

## PEACOCK ONE VERIFICATION

```text
PEACOCK ONE VERIFICATION

Backend: PASS
Database: PASS
Crawler: PASS
SEO: PASS
AEO: FAIL
GEO: FAIL
AI Visibility: FAIL
Multi-LLM Gateway: PARTIAL
PINE: PASS
Peacock Council: PASS
Peacock Judge: PASS
Competitor Intelligence: PASS
Content Intelligence: PASS
Writer Intelligence: PASS
Peacock 90: PASS
Monitoring: FAIL
Learning Engine: PASS
Ask Peacock: PASS
Security: FAIL
Tests: 226 passed / 0 failed
Production Build: PASS
Production Readiness: 62/100
```
