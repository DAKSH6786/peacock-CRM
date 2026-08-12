# Peacock Temporal Intelligence

Understands **change** via a **Visibility Timeline** and statistical change-point detection.

## Visibility Timeline tracks

| Kind | Label |
| --- | --- |
| `search_change` | Search changes |
| `ai_answer_change` | AI answer changes |
| `citation_change` | Citation changes |
| `competitor_change` | Competitor changes |
| `entity_change` | Entity changes |
| `sentiment_change` | Sentiment changes |
| `content_update` | Content updates |
| `algorithm_event` | Algorithm events |
| `peacock_action` | Peacock actions |

## Supported queries

- “What changed?”
- “Why did visibility drop?”
- “What happened before citations increased?”
- “Which action preceded our ranking increase?”

Answers cite supporting timeline events and note temporal precedence ≠ causality.

## Change-point detection

Where series volume allows, Peacock runs a CUSUM / z-score hybrid:

- Requires sufficient baseline points
- Alerts only when z-score and effect size clear noise floors
- **Does not alert on meaningless noise** (`suppressed_as_noise`)

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/temporal/catalog` | Event kinds, example queries, detection thresholds |
| `POST` | `/temporal/timelines` | Build timeline + detect + answer queries |
| `GET` | `/temporal/timelines/{id}` | Retrieve |

## Tables

`temporal_timelines`, `ti_timeline_events`, `ti_change_points`, `ti_query_answers`
