# Probabilistic AI Visibility

**Do not measure AI visibility from one prompt response.**

Generative systems are probabilistic. The same prompt can produce different
brands, citations, and ordering across repeated runs.

Peacock One therefore estimates **distributions** from controlled,
rate-limited repetitions.

## Controlled cell

For strategically important prompts:

| Dimension | Example |
| --- | --- |
| Prompt `P` | “best enterprise SEO platform” |
| Model / engine `M` | chatgpt, perplexity, gemini, … |
| Location `L` | `us`, `uk`, `global` |
| Persona `A` | `seo_lead`, `cmo` |
| Temperature / config `C` | `temp_0.2` |
| Time `T` | observation period / bucket |

Run 1…N (configurable repetitions).

## Anti-abuse

Every campaign has hard ceilings:

- `target_repetitions` / `max_repetitions` (hard max 50)
- `max_calls_per_minute` (hard max 30)
- `max_concurrent` (hard max 3)
- `max_total_calls` (hard max 2000)
- `min_interval_ms` (hard min 500)

Uncontrolled API traffic is rejected.

## Distributional metrics

Instead of a single boolean:

| Metric | Example |
| --- | --- |
| Brand Mention Probability | 0.74 |
| Citation Probability | 0.31 |
| Top-3 Recommendation Probability | 0.46 |
| Competitor A Probability | 0.82 |
| Competitor B Probability | 0.65 |

Also computed per metric:

- variance
- confidence interval
- sample size
- engine disagreement
- temporal volatility
- **PEACOCK VISIBILITY CONFIDENCE**

## Score card display

```text
AI Visibility Score: 68
Measurement Confidence: HIGH

Based on:
450 observations
5 engines
90 prompts
multiple observation periods
```

Single-shot measurements are never presented as HIGH confidence.

## API

- `GET /visibility/status`
- `POST /visibility/campaigns`
- `POST /visibility/campaigns/{id}/run`
- `GET /visibility/campaigns/{id}/score`

## Code

- ORM: `packages/db_models/probabilistic_visibility.py`
- Service: `services/geo_engine/probabilistic_*.py`
- Migration: `database/migrations/versions/0009_probabilistic_visibility.py`
