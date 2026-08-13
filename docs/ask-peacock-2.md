# Ask Peacock 2.0

Natural-language interface over the entire Peacock **intelligence graph**.

## Example questions

- Why is Competitor A beating us?
- What should we do with ₹10 lakh over the next 90 days?
- Which ten pages could generate the highest GEO improvement?
- Which writer should write Topic X?
- Where is our weakest generative engine?
- What external sources are influencing AI opinions about us?
- What changed this week?
- What should the CEO know?

## Answer structure

Every answer is structured into:

| Section | Role |
| --- | --- |
| **OBSERVED** | What the graph currently shows |
| **INFERRED** | Interpretation (not certainty) |
| **RECOMMENDED** | What to do next |
| **FORECAST** | Directional range / outlook |
| **CONFIDENCE** | 0–1 score + rationale |

Each answer includes **evidence** citations into graph surfaces (competitor, SoA, citation graph, temporal, anomaly, Peacock 90, writer intelligence, etc.).

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/ask-peacock/catalog` | Intents, sections, example questions, surfaces |
| `POST` | `/ask-peacock/sessions` | Ask one or more questions |
| `GET` | `/ask-peacock/sessions/{id}` | Retrieve session |

Empty `questions` runs the full example set against demo graph signals.

## Tables

`ask_peacock_sessions`, `ap_answers`, `ap_evidence`
