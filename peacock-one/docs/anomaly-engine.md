# Peacock Anomaly Engine

Detects unusual shifts and **ranks anomalies by probable business impact**.

## Detects

| Type | Label |
| --- | --- |
| `sudden_ranking_loss` | Sudden ranking loss |
| `ai_visibility_collapse` | AI visibility collapse |
| `citation_disappearance` | Citation disappearance |
| `negative_sentiment_spike` | Negative sentiment spike |
| `competitor_acceleration` | Competitor acceleration |
| `crawler_issue` | Crawler issue |
| `indexation_loss` | Indexation loss |
| `traffic_anomaly` | Traffic anomaly |
| `backlink_loss` | Backlink loss |

## Business impact ranking

Each anomaly receives an `impact_score` (0–100) and `impact_rank` from:

- type impact priors (e.g. ranking/traffic weighted higher)
- severity (`low` → `critical`)
- signal strength (z-score / relative change)
- optional revenue exposure

Not a guaranteed P&L forecast — probable impact for triage.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/anomalies/catalog` | Types, priors, ranking note |
| `POST` | `/anomalies/scans` | Run detection + ranking |
| `GET` | `/anomalies/scans/{id}` | Retrieve scan |

## Tables

`anomaly_scans`, `ae_anomalies`
