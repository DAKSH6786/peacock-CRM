# Peacock Executive Brain

Special **executive view** — not an SEO complexity display.

## Questions

- Where are we winning?
- Where are we losing?
- Why?
- What changed?
- What is worth doing?
- What will it cost?
- What could it return?
- What happens if we do nothing?

## Summaries

Generates **CEO-ready** and **CMO-ready** briefs with a clear decision / call to action. Returns and confidence are directional ranges — not guaranteed P&L.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/executive-brain/catalog` | Question catalog |
| `GET` | `/executive-brain/preview` | Public demo brief for the UI |
| `POST` | `/executive-brain/briefs` | Persist a brief |
| `GET` | `/executive-brain/briefs/{id}` | Retrieve brief |

## UI

`/executive` — Peacock Executive Brain (linked from Command Centre)

## Tables

`executive_brain_briefs`, `eb_answers`, `eb_role_summaries`
