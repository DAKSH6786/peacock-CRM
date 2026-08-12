# Share of Answer

Traditional tools measure **Share of Voice**.

Peacock One additionally measures **Share of Answer** — how much of a
generative answer is controlled by or favourable to each brand/entity.

## Example

Query Cluster: **Enterprise CRM**

| Brand | Share of Answer |
| --- | ---: |
| Brand A | 34% |
| Brand B | 28% |
| Client | 11% |

## Methodology

**Do not pretend token count alone equals influence.**

Extraction uses heuristic answer-text analysis (mention spans, list/first-appearance
rank, recommendation language, sentence/slot share, citation cues, claim polarity,
comparison language). Token span ratio is diagnostic only.

Share of Answer combines multiple indicators:

| Indicator | Role |
| --- | --- |
| Mention | Whether the entity appears |
| Position | Rank / order in recommendations |
| Recommendation strength | How strongly the answer endorses the entity |
| Answer space | Structural slot / section presence (not raw tokens-as-influence) |
| Citation ownership | Whether citations / sources belong to the entity |
| Semantic prominence | Salience of the entity in the answer narrative |
| Positive / negative / neutral claims | Claim polarity counts |
| Comparison outcome | win / lose / tie / mixed / absent |

Token span ratio is stored as a **diagnostic** signal and compared via
`token_only_share` / `token_vs_influence_gap`. It is never the sole
methodology (`token_count_alone_rejected = true`).

Default influence weights (sum ≈ 1.0):

| Indicator | Weight |
| --- | ---: |
| recommendation_strength | 0.18 |
| position | 0.14 |
| citation_ownership | 0.14 |
| mention | 0.12 |
| semantic_prominence | 0.12 |
| answer_space | 0.10 |
| claim_balance | 0.10 |
| comparison_outcome | 0.10 |

Per-answer influence is averaged across observations, then normalised so
brand shares sum to ~100% within the query cluster.

## Relational model

| Table | Role |
| --- | --- |
| `share_of_answer_analyses` | Query-cluster analysis run |
| `soa_answer_observations` | Generative answers analysed |
| `soa_entity_indicators` | Per-entity multi-indicator readings |
| `soa_brand_scores` | Aggregated Share of Answer % |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/share-of-answer/catalog` | Indicators + default weights |
| `POST` | `/share-of-answer/analyses` | Run analysis |
| `GET` | `/share-of-answer/analyses/{id}` | Retrieve report |

Response includes `example_display` for cluster leaderboards and full
per-brand indicator breakdowns.
