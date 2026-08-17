# Peacock Learning Engine 2.0

The long-term moat: learn from every recommendation lifecycle.

## Closed loop (stored for every recommendation)

1. **Context**
2. **Recommendation**
3. **Expected Impact**
4. **Confidence**
5. **Execution**
6. **Actual Outcome**

## What Peacock learns

| Question | Dimension |
| --- | --- |
| Which topics work? | `topic` |
| Which formats work? | `format` |
| Which sources matter? | `source` |
| Which writers succeed? | `writer` |
| Which interventions improve citation? | `citation_intervention` |
| Which industries behave differently? | `industry` |
| Which engines respond differently? | `engine` |

## Industry-specific learning

Policies are maintained separately for:

Finance · Healthcare · SaaS · E-commerce · Education · Travel · Legal · Consumer goods · Technology

**Do not apply one universal GEO strategy.** Each industry policy forbids universal GEO claims and prefers industry-local formats, sources, and citation interventions.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/learning2/catalog` | Industries, dimensions, loop fields |
| `POST` | `/learning2/records` | Create closed-loop record |
| `GET` | `/learning2/records/{id}` | Retrieve |
| `POST` | `/learning2/records/{id}/execution` | Record execution |
| `POST` | `/learning2/records/{id}/outcome` | Record actual outcome |
| `POST` | `/learning2/runs` | Learn insights + refresh industry policies |
| `GET` | `/learning2/policies` | List industry policies |

## Tables

`learning2_records`, `le2_context_factors`, `le2_industry_policies`, `le2_dimension_insights`, `le2_learning_runs`
