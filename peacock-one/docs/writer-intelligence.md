# Writer Intelligence 2.0

Proprietary writer decision system — **not** sample embedding similarity.

## Decision question

> Which writer is most likely to produce the **best outcome** for **THIS topic**, for **THIS client**, for **THIS audience**?

Not: “Who writes similarly?”

## Writer DNA

Analyse (0–100):

| Trait | Trait | Trait |
| --- | --- | --- |
| Subject expertise | Research depth | Technical accuracy |
| Style | Tone | Sentence structure |
| Readability | Storytelling | Citations |
| Fact density | Original thinking | SEO execution |
| AEO execution | GEO execution | Editing effort |
| Deadline reliability | Client acceptance | |

## Writer × Topic × Client model

Predicted outcome blends:

- DNA fit for the brief (incl. SEO/AEO/GEO needs)
- Topic fit (prior topics / subject tags)
- Client / industry fit
- Audience fit
- Historical pathway outcomes from the Outcome Graph

`similarity_not_used_as_primary=true` on every recommendation. Similarity-only matching is explicitly rejected.

## Writer Outcome Graph

```
Writer → Article → Client → Industry → Topic → Performance
```

Performance signals: approval, revision rounds, ranking, impressions, AI citations, engagement, links earned, conversion (where available).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/writer-intelligence/catalog` | DNA traits, graph kinds, methodology |
| `POST` | `/writer-intelligence/analyses` | Run decision |
| `GET` | `/writer-intelligence/analyses/{id}` | Retrieve report |

## Tables

`writer_intelligence_analyses`, `wi_writer_dna`, `wi_dna_traits`, `wi_outcome_nodes`, `wi_outcome_edges`, `wi_performance_records`, `wi_recommendations`
