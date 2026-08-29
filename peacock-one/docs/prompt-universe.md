# Prompt Universe Intelligence

Competitors usually track a **manually configured** prompt set (25 / 50 / 100).

Peacock One builds a **Prompt Universe** — the complete intent landscape for a
brand — then tracks both short discovery prompts and persona-contextual ones.

## Sources

Prompt families are generated from:

| Source | `source_kind` |
| --- | --- |
| Products | `product` |
| Services | `service` |
| Keywords | `keyword` |
| Search Console queries | `search_console_query` |
| Competitor rankings | `competitor_ranking` |
| Forums | `forum` |
| SERPs | `serp` |
| People Also Ask | `people_also_ask` |
| Customer personas | `customer_persona` |
| Funnel stages | `funnel_stage` |
| Locations | `location` |
| Industry concepts | `industry_concept` |
| AI query patterns | `ai_query_pattern` |
| Prompt taxonomy | `prompt_taxonomy` |

## Prompt taxonomy fields

Every universe prompt stores:

- `topic` / `subtopic`
- `intent`
- `persona` (`persona_code`)
- `funnel_stage`
- `location`
- `product`
- `problem`
- `commercial_value`
- `brand_relevance`
- `prompt_type`

### Prompt types

Discovery · Recommendation · Comparison · Problem Solving · Purchase · Research ·
Validation · Alternative · Pricing · Trust · Risk · Technical · Educational ·
Transactional

(Stored as lowercase snake_case, e.g. `problem_solving`.)

## Synthetic personas

Analytical query lenses — **not** fake real identities:

| Code | Name |
| --- | --- |
| `cfo` | CFO |
| `cmo` | CMO |
| `student` | Student |
| `enterprise_buyer` | Enterprise buyer |
| `technical_evaluator` | Technical evaluator |
| `hnwi` | HNWI |
| `small_business_owner` | Small business owner |
| `developer` | Developer |
| `parent` | Parent |
| `healthcare_professional` | Healthcare professional |

## Simple + contextual (track both)

**Simple**

```text
best CRM
```

**Contextual (enterprise buyer / technical evaluator style)**

```text
We are a 1,500 employee SaaS company migrating from Salesforce
and require European data residency.
Which CRM platforms should we shortlist?
```

Peacock stores both under the same prompt family, with `complexity=simple|contextual`.

## Relational model

| Table | Role |
| --- | --- |
| `prompt_universes` | Container per website / brand |
| `synthetic_personas` | Materialised analytical personas |
| `prompt_source_signals` | Ingested seed signals |
| `prompt_families` | Intent clusters |
| `universe_prompts` | Fully tagged prompts |
| `prompt_generation_runs` | Expansion audit trail |

`visibility_probe_cells.universe_prompt_id` optionally links probabilistic
visibility measurement back into the universe.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/prompt-universe/catalog` | Types, sources, personas |
| `POST` | `/prompt-universe/universes` | Create + generate |
| `GET` | `/prompt-universe/universes/{id}` | Summary |
| `POST` | `/prompt-universe/universes/{id}/expand` | Add signals |
| `GET` | `/prompt-universe/universes/{id}/prompts` | List / filter |
| `GET` | `/prompt-universe/universes/{id}/personas` | Personas |

Filter prompts with `prompt_type`, `persona_code`, `complexity`, `tracked_only`.
