# Peacock Moat Data Model

Proprietary intelligence accumulation layer — Peacock One's long-term competitive advantage.

Domain engines remain systems of record. Moat tables unify closed-loop pathway memory across products.

## Pathway kinds

| Kind | Chain |
| --- | --- |
| `recommendation_outcome` | recommendation → outcome |
| `writer_topic_outcome` | writer → topic → outcome |
| `citation_source_visibility` | citation source → AI visibility |
| `content_structure_citation` | content structure → citation result |
| `industry_geo_strategy_result` | industry → GEO strategy → result |
| `entity_gap_intervention_result` | entity gap → intervention → result |
| `competitor_movement_response_outcome` | competitor movement → response → outcome |

## Design rules

- Typed nodes (`stimulus` / `intervention` / `mediator` / `result`) with directed edges
- Outcomes attach measured deltas with provenance back to source systems
- Industry → GEO pathways are **industry-scoped** — Peacock does not claim a universal GEO strategy
- Moat strength scores coverage × confidence × outcome signal

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/moat-data-model/catalog` | Pathway kinds, roles, edge types, positioning |
| `GET` | `/moat-data-model/preview` | Demo accumulation of all seven pathway kinds |
| `POST` | `/moat-data-model/runs` | Persist a moat intelligence accumulation run |
| `GET` | `/moat-data-model/runs/{id}` | Retrieve a moat run with pathways |

## Tables

`moat_intelligence_runs`, `moat_pathways`, `moat_pathway_nodes`, `moat_pathway_edges`, `moat_pathway_outcomes`

## Positioning

This dataset becomes Peacock One's long-term competitive advantage: closed-loop memory that competitors cannot easily replicate from public SEO tools alone.
