# Peacock Council 2.0

Multi-model council for **major decisions** using **opposing assigned roles**.

## Do not ask «What do you think?»

Open opinion prompts are rejected. Each agent receives a role mandate, e.g.:

| Role | Mandate focus |
| --- | --- |
| SEO Researcher | Search demand / rankability |
| GEO Researcher | Generative visibility / citability |
| Business Strategist | Commercial upside / trade-offs |
| Competitor Analyst | Rival gaps / competitive risk |
| Evidence Reviewer | Provenance / evidence quality |
| Sceptic | Challenge weak claims |
| Risk Analyst | Downside / failure modes |

## Debate protocol

1. **Independent analysis**
2. **Each agent receives structured summaries from others**
3. **Identify disagreements**
4. **Request evidence specifically for disputed claims**
5. **Judge**

## Storage contract

**Never expose or persist hidden chain-of-thought.**

Store only:

- claim
- evidence
- counterargument
- confidence
- decision

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/council2/catalog` | Roles, rounds, storage rules |
| `POST` | `/council2/sessions` | Run opposing-role debate |
| `GET` | `/council2/sessions/{id}` | Retrieve structured artifacts |

## Tables

`council2_sessions`, `c2_agents`, `c2_round_records`, `c2_claims`, `c2_evidence`, `c2_counterarguments`, `c2_disagreements`, `c2_evidence_requests`, `c2_decisions`
