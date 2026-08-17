# Peacock One Quality Bar

Before considering any module complete, ask:

| Gate question | If yes |
| --- | --- |
| Does this merely match a conventional SEO tool? | Improve it. |
| Does this merely track AI mentions? | Improve it. |
| Does this only give an LLM recommendation? | Add evidence. |
| Does it have evidence but no uncertainty? | Add confidence. |
| Does it recommend something but never measure the result? | Add outcome tracking. |
| Does it track results but never learn from them? | Connect it to Peacock Learning. |
| Does an expensive LLM call perform something deterministic code could calculate? | Move it out of the LLM. |

A module is **complete** only when all seven gates pass (answering each “merely/only/never” question with **no**).

## Verdicts

| Verdict | Meaning |
| --- | --- |
| `complete` | All gates passed |
| `incomplete` | Some gates failed — remediations listed |
| `blocked` | Zero gates passed |

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/quality-bar/catalog` | Gates, questions, improvements, module catalog |
| `GET` | `/quality-bar/preview` | Demo (LLM-only recommender fails evidence→learning) |
| `POST` | `/quality-bar/assessments` | Persist an assessment |
| `GET` | `/quality-bar/assessments/{id}` | Retrieve assessment |

## Tables

`quality_bar_assessments`, `qb_gate_results`, `qb_remediation_actions`

## Related

- Peacock Learning Engine 2.0 — learning-loop remediation target  
- Evidence Ledger — evidence-backed recommendations  
- Cost Intelligence — keep deterministic work out of LLMs  
- Moat Data Model — recommendation → outcome pathways  
