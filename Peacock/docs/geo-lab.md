# Peacock GEO Lab

Controlled generative-engine experimentation — a competitive moat for measuring what content changes *may* contribute to visibility, without false causal claims.

## Experiment variants

| Version | Treatment |
| --- | --- |
| **A** | Original page (baseline) |
| **B** | Improved evidence |
| **C** | Better structured answers |
| **D** | Original dataset added |

Custom variants are also supported.

## Metrics (before / after)

- SEO
- Retrieval
- AI mention
- AI citation
- Answer prominence
- Organic performance

## Experiment design support

- **Control pages** vs **test pages**
- **Matched groups** (topic/intent pairing)
- **Before / after** windows
- **Time series** observations (`pre` / `during` / `post`)

## Causality warning

**Do NOT automatically conclude that Change X caused a visibility improvement.**

GEO Lab distinguishes, from weakest to strongest:

| Level | Meaning |
| --- | --- |
| Correlation | Co-movement only |
| Likely contribution | Test moved differently from controls |
| Controlled experiment | Controls + matched groups + before/after |
| Causal evidence | Strongest careful label — still **rejects** auto “X caused Y” slogans |

Every assessment sets `auto_causal_conclusion_rejected=true` and includes the full causality warning text.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/geo-lab/catalog` | Variants, metrics, causality levels, warning |
| `POST` | `/geo-lab/experiments` | Run controlled experiment analysis |
| `GET` | `/geo-lab/experiments/{id}` | Retrieve experiment report |

## Tables

`geo_lab_experiments`, `gl_variants`, `gl_pages`, `gl_metric_observations`, `gl_metric_deltas`, `gl_causality_assessments`
