# Peacock execution modes

PINE runs under one of five operational modes. Every mode declares a hard
budget envelope:

| Field | Meaning |
| --- | --- |
| `max_cost` | Ceiling in USD micros |
| `max_calls` | Max model / tool calls |
| `max_iterations` | Max pipeline iterations / loops |
| `max_runtime` | Wall-clock seconds |

Modes are **policies**, not permanent model-role locks.

## Modes

### Peacock Fast
Single-pass. Low cost. Simple analyses.
Skips research, critic, and simulation by default.

### Peacock Standard
Multiple evidence sources. One primary reasoning model.
Verification when required (skipped for low-risk asks without challenges).

### Peacock Deep
Several agents. Multiple models. Research. Critic. Verification.

### Peacock Council
Strategic decisions. Independent models. Adversarial reasoning.
Evidence reconciliation.

### Peacock Lab
Experimental research mode. Can perform:
- repeated measurements
- prompt experiments
- content simulations
- controlled comparisons
- hypothesis tests

Product surface: **Peacock Research Mode** (`/research` UI, `/research-mode` API) —
define hypothesis, metric, pages, prompts; collect baseline; measure treatment;
repeat observations; calculate uncertainty; generate findings.

## Budgets (defaults)

| Mode | max_cost | max_calls | max_iterations | max_runtime |
| --- | ---: | ---: | ---: | ---: |
| Fast | 5_000 | 12 | 1 | 30s |
| Standard | 25_000 | 12 | 3 | 120s |
| Deep | 100_000 | 40 | 8 | 600s |
| Council | 200_000 | 60 | 12 | 900s |
| Lab | 150_000 | 80 | 20 | 1200s |

## API

- `GET /intelligence/modes`
- `POST /intelligence/runs` with optional `peacock_mode`
- Mode + budget usage returned on each run as `peacock_mode` / `mode`

## Code

- `services/intelligence/peacock_modes.py`
- Wired through Layer 0 classification and `StrategicPipeline`
