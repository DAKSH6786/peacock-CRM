# Retrieval Pathway Intelligence

Explain **why** a page may not be cited — not merely that it wasn't.

Peacock does **not** claim access to proprietary internal ranking algorithms of
third-party AI companies. Outputs use careful terminology:

- **inferred retrieval pathway**
- **observed evidence**
- **estimated likelihood**

## Example

```text
LIKELY VISIBILITY BOTTLENECK

Retrieval probability       HIGH
Citation selection          LOW

Interpretation:
Your page appears strongly relevant,
but competing sources are substantially more likely to be cited.

Recommended investigation:
citation-quality gap.
```

## Possible causes (with uncertainty)

| Cause code | Meaning |
| --- | --- |
| `page_unavailable` | Page unreachable / error status |
| `crawl_restricted` | robots / noindex style restrictions |
| `weak_topical_relevance` | Weak match to query cluster |
| `insufficient_entity_relationship` | Thin brand–topic entity links |
| `competitor_page_stronger` | Competitors dominate comparative signals |
| `source_freshness` | Stale relative to alternatives |
| `poor_extractability` | Hard for machines to extract clean answers |
| `insufficient_supporting_evidence` | Thin on-page support |
| `lack_of_third_party_corroboration` | Few third-party reinforcements |
| `content_not_retrieved` | Likely absent from inferred retrieval set |
| `content_retrieved_but_not_selected` | Present/relevant but not chosen for citation |
| `brand_mentioned_but_not_cited` | Mention without page citation |

Each classification includes **estimated likelihood**, **likelihood band**,
**uncertainty**, supporting/contrary observed evidence, and a rationale.

## Pathway likelihoods

Two headline estimated likelihoods (0–1 → bands VERY_LOW…VERY_HIGH):

1. **Estimated retrieval likelihood** — availability, crawl access, relevance, extractability, freshness, observed retrieval cues
2. **Estimated citation selection likelihood** — citation rate, corroboration, supporting evidence, entity strength, competitor gap

## Relational model

| Table | Role |
| --- | --- |
| `retrieval_pathway_analyses` | Forensic analysis run |
| `rpi_evidence` | Observed evidence rows |
| `rpi_cause_classifications` | Cause likelihoods + uncertainty |
| `rpi_bottleneck_diagnoses` | Headline bottleneck diagnosis |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/retrieval-pathway/catalog` | Causes, bands, disclaimer |
| `POST` | `/retrieval-pathway/analyses` | Run forensics |
| `GET` | `/retrieval-pathway/analyses/{id}` | Retrieve report |

`proprietary_ranking_access_claimed` is always `false`.
