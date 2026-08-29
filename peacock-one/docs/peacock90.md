# Peacock 90 2.0

Adaptive **90-day roadmap** that functions as an **optimisation engine**.

## Inputs (constraints)

| Input | Role |
| --- | --- |
| Available budget | Hard spend ceiling (e.g. ₹X) |
| Writers | Content headcount |
| Developers | Engineering headcount |
| SEO team | SEO specialist headcount |
| Content capacity | Max articles/month |
| Approval capacity | Approvals/week |
| Business priorities | Ordered priority families |
| Risk tolerance | `low` \| `medium` \| `high` |

## Behaviour

Generates the **maximum-impact roadmap within those constraints**.

### Resource optimisation

Example available:

- 2 developers  
- 5 writers  
- 1 SEO specialist  
- Maximum **25 articles/month**  
- Budget ₹X  

Peacock **must not** recommend **100 articles** if the organisation cannot execute them. Infeasible aspirational plans are recorded as **capacity refusals**.

### Dependency graph

Tasks understand dependencies. Example:

```
Fix canonical issue
        ↓
Recrawl
        ↓
Update content
        ↓
Request indexing
        ↓
Monitor
```

Predecessors are scheduled before successors across the ~13-week horizon.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/peacock90/catalog` | Constraints, example resources, dependency example |
| `POST` | `/peacock90/plans` | Optimise and persist adaptive roadmap |
| `GET` | `/peacock90/plans/{id}` | Retrieve plan |

## Tables

`peacock90_plans`, `p90_initiatives`, `p90_tasks`, `p90_dependencies`, `p90_capacity_refusals`
