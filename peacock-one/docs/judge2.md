# Peacock Judge 2.0

Deterministic multi-signal judgment for major recommendations.

## Combines

| Signal | Role |
| --- | --- |
| Deterministic data | Measured / structured inputs |
| Statistical evidence | Quantified lifts / distributions |
| Historical outcomes | Prior realized results |
| Multi-model findings | Council / model consensus |
| Source reliability | Evidence provenance quality |
| Business goals | Commercial alignment |
| Cost | Resource burden (inverted) |
| Risk | Downside (inverted) |
| Confidence | Trust in the brief |

**Scoring runs outside the LLM where possible** (`scoring_outside_llm=true`).

## Returns

1. **Recommended Action**
2. **Why**
3. **Evidence**
4. **Expected Upside**
5. **Risk**
6. **Confidence**
7. **Alternative**
8. **What Would Change Our Decision** ← required reversal triggers

### Example — What Would Change This Recommendation?

> If keyword demand declines >40%  
> **or**  
> if Competitor A loses citation dominance  
> **re-evaluate.**

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/judge2/catalog` | Signals, weights, output fields |
| `POST` | `/judge2/judgments` | Run deterministic judgment |
| `GET` | `/judge2/judgments/{id}` | Retrieve judgment |

## Tables

`judge2_judgments`, `j2_signal_scores`, `j2_evidence`, `j2_reversal_conditions`
