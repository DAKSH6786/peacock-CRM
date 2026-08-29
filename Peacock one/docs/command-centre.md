# Peacock Command Centre

Flagship UI for Peacock One. **Not** a generic SEO dashboard.

## Home composition

**Peacock Command Centre**

### Top — Peacock Visibility Index

- Search Visibility
- AI Visibility
- Share of Answer
- Entity Authority
- Citation Authority
- Content Opportunity
- Agent Readiness

### Second layer — Situation

- Biggest Opportunity
- Biggest Threat
- Fastest Win
- Competitor Movement
- AI Visibility Change
- Critical Technical Issue

### Intelligence feed

Detections in this form:

```
PEACOCK DETECTED

Competitor A increased citation share
from 18% → 31%.

Primary driver:
3 recently published research pages.

Potential response:
Publish proprietary benchmark study.

Confidence:
87%
```

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/command-centre/catalog` | Dimensions + situation kinds |
| `GET` | `/command-centre/preview` | Public demo snapshot for the UI |
| `POST` | `/command-centre/snapshots` | Persist a snapshot |
| `GET` | `/command-centre/snapshots/{id}` | Retrieve snapshot |

## UI

- Home (`/`) — Command Centre
- `/ops` — crawl / audit / platform tooling

## Tables

`command_centre_snapshots`, `cc_visibility_signals`, `cc_situation_items`, `cc_feed_items`
