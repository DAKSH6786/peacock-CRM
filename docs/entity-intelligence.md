# Peacock Entity Intelligence

Upgrade of the knowledge-graph concept into a generative-visibility entity graph.

## Tracked entity types

Brand · Founder · Executives · Products · Services · People · Industry · Problems ·
Locations · Competitors · Features · Publications · Concepts · Customers · Topics ·
Pages · Sources

## Entity Association Strength

Multi-signal, explainable score (0–1) for pairs such as brand ↔ product/concept.

Example (Entity Ownership view):

| Pair | Strength |
| --- | ---: |
| HSBC ↔ Premier Banking | 0.91 |
| HSBC ↔ Wealth Management | 0.84 |
| HSBC ↔ Student Banking | 0.61 |

Components:

| Signal | Default weight |
| --- | ---: |
| co_occurrence | 0.20 |
| ownership_signal | 0.18 |
| semantic_proximity | 0.16 |
| citation_linkage | 0.12 |
| topical_centrality | 0.12 |
| cross_source_consistency | 0.12 |
| recency | 0.10 |

Compare the same target concepts across competitors.

## Entity Gap

Example:

```text
Target Concept: International Wealth Management

Competitor A association     0.87
Competitor B association     0.79
Client association           0.42
```

Gap size = leading competitor − client. Severity drives strategy priority.

## Strategy generation

From gaps, Peacock recommends actions such as:

- strengthen entity ownership
- publish pillar content
- earn third-party association
- clarify product positioning
- executive thought leadership
- close feature narrative gap
- localise entity presence
- competitor differentiation

## Relational model

| Table | Role |
| --- | --- |
| `entity_intelligence_analyses` | Analysis run |
| `ei_entities` | Graph nodes |
| `ei_associations` | Association Strength edges |
| `ei_entity_gaps` | Client vs competitor gaps |
| `ei_strategies` | Generated strategy |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/entity-intelligence/catalog` | Types, components, weights |
| `POST` | `/entity-intelligence/analyses` | Build graph + gaps + strategy |
| `GET` | `/entity-intelligence/analyses/{id}` | Retrieve report |
