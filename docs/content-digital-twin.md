# Content Digital Twin

Pre-publish simulation of a proposed article against multi-channel requirements.

## Simulate against

| Surface | Purpose |
| --- | --- |
| SEO requirements | Keywords, on-page / structural SEO expectations |
| AEO requirements | Answer-engine eligibility (FAQ, definitions, direct answers) |
| GEO requirements | Generative visibility (entities, evidence, structure) |
| Competitor pages | Rival strengths, questions, entities, evidence types |
| Target entities | Required brand/product/topic entities |
| User personas | Intents and questions the article must serve |
| AI answer scenarios | Prompts and must-include points/entities |
| Citation requirements | Attribution / quotable source expectations |
| Brand guidelines | Tone, required mentions, forbidden claims |

## Outputs

Every evaluation produces:

- **Predicted Strength** — composite coverage across surfaces
- **Potential Weaknesses** — requirement gaps and brand risks
- **Missing Entities** — target / scenario / competitor entities absent from the plan
- **Missing Evidence** — evidence types and claims not planned
- **Missing Questions** — persona, AEO, AI, or competitor questions uncovered
- **Competitor Advantages** — rival lead dimensions
- **Citation Opportunities** — places to add attributable sources
- **Differentiation Opportunities** — angles to deepen vs competitors

Also returns per-surface **coverage scores**, **readiness score**, and a summary.

Scores are Peacock estimates for editorial planning — not live SERP/AI guarantees.

## Modify plan and rerun

1. Create a twin with an article plan + simulation context → initial evaluation
2. `PATCH /content-digital-twin/twins/{id}/plan` with an updated plan (`rerun: true` by default)
3. Or `POST /content-digital-twin/twins/{id}/evaluations` to rerun without changing the plan

Each run increments `evaluation_number` and snapshots the plan/context used.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/content-digital-twin/catalog` | Surfaces + finding categories |
| `POST` | `/content-digital-twin/twins` | Create twin + evaluate |
| `GET` | `/content-digital-twin/twins/{id}` | Twin + latest evaluation + history |
| `PATCH` | `/content-digital-twin/twins/{id}/plan` | Modify plan (optional rerun) |
| `POST` | `/content-digital-twin/twins/{id}/evaluations` | Rerun evaluation |
| `GET` | `/content-digital-twin/twins/{id}/evaluations/{eval_id}` | Historical evaluation |

## Tables

`content_digital_twins`, `cdt_evaluations`, `cdt_requirement_scores`, `cdt_findings`
