# Peacock Citation Graph

Map generative citation pathways and aggregate them across thousands of
observations.

## Pathway

```text
AI Engine
  ↓
Prompt
  ↓
Answer
  ↓
Citation
  ↓
Domain
  ↓
Page
  ↓
Entity
  ↓
Topic
```

## Discover

Across a topic cluster, Peacock surfaces:

- most influential citation domains
- citation hubs
- citation pathways
- competitor-owned sources
- independent sources
- news / forums / review sites
- government / academic / industry publications

## Citation Influence Score (CIS)

Proprietary, **fully explainable** multi-component metric (0–100):

| Component | Default weight | Meaning |
| --- | ---: | --- |
| citation_frequency | 0.18 | How often the domain is cited vs observation volume |
| cross_engine_citation | 0.14 | Presence across generative engines |
| topic_coverage | 0.12 | Breadth of topic labels covered |
| prominence | 0.12 | In-answer emphasis / position |
| freshness | 0.10 | Recency of cited material (unknown → neutral) |
| authority_proxy | 0.12 | Explainable source-class prior (+ optional trust) |
| brand_association | 0.12 | Client co-mention rate when domain is cited |
| citation_diversity | 0.10 | Distinct pages/engines vs raw citation volume |

Each component stores a human-readable explanation string. There is no opaque
black-box residual.

## Source Opportunity Engine

When models repeatedly cite **Domain X** while the client brand is absent or weak:

> This source influences 27% of AI answers in this topic cluster.  
> Your brand is mentioned in 2%.  
> Competitor A is mentioned in 64%.

Peacock may recommend **only ethical actions**:

- PR opportunity
- expert contribution
- original research
- source partnership
- listing correction
- review improvement
- content relationship

**Never** suggests manipulative spam, link farms, fake reviews, cloaking,
astroturfing, or undisclosed paid placements (`manipulative_spam_rejected = true`).

## Relational model

| Table | Role |
| --- | --- |
| `citation_graph_analyses` | Topic-cluster analysis run |
| `cg_observations` | Engine + prompt + answer |
| `cg_citations` | Citation → domain → page |
| `cg_entity_mentions` | Client / competitor / entity presence |
| `cg_pathways` | Materialised full pathway rows |
| `cg_domain_scores` | Aggregated CIS + hub flags |
| `cg_source_opportunities` | Ethical opportunity findings |

Optional FKs link observations to `visibility_probe_observations`,
`ai_query_runs`, and legacy `citation_observations`.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/citation-graph/catalog` | Pathway, CIS weights, opportunity types |
| `POST` | `/citation-graph/analyses` | Build graph + CIS + opportunities |
| `GET` | `/citation-graph/analyses/{id}` | Retrieve report |
