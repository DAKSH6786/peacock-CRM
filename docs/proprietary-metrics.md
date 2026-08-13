# Peacock Proprietary Metrics

Documented scoring framework for Peacock One.

## IMPORTANT

These are **Peacock proprietary indicators**.

They are **NOT**:

- Google ranking factors
- OpenAI / ChatGPT ranking factors
- Anthropic / Claude ranking factors
- Perplexity ranking factors
- Any other platform’s official algorithms

Peacock does **not** claim access to proprietary third-party ranking systems.

---

## Metrics & formulas

Every formula is also exposed via `GET /proprietary-metrics/catalog` and attached to each scored metric (`formula_id`, `formula_text`).

### 1. Peacock Visibility Index — `PVI-1`

```
PVI = mean(Search Visibility, AI Visibility, Share of Answer,
           Entity Authority, Citation Authority, Content Opportunity,
           Agent Readiness)
```

Equal-weight mean of seven Peacock dimensions (each 0–100).

### 2. Peacock AI Visibility Score — `PAIVS-1`

```
PAIVS = 100 * (0.35*SoA_norm + 0.25*CIS_norm
             + 0.20*EntityAuth_norm + 0.20*Citability_norm)
```

Composite of Peacock SoA, CIS, Entity Authority, Generative Citability.

### 3. Share of Answer — `SOA-1`

```
SoA = 100 * Σ_i (w_i * indicator_i)
```

Indicators: mention, position, recommendation_strength, answer_space, citation_ownership, semantic_prominence, claim_balance, comparison_outcome.

Default weights: `0.12, 0.14, 0.18, 0.10, 0.14, 0.12, 0.10, 0.10`.

**Token count alone is rejected.**

### 4. Citation Influence Score — `CIS-1`

```
CIS = 100 * Σ_i (w_i * component_i)
```

Components: citation_frequency, cross_engine_citation, topic_coverage, prominence, freshness, authority_proxy, brand_association, citation_diversity.

Default weights: `0.18, 0.14, 0.12, 0.12, 0.10, 0.12, 0.12, 0.10`.

### 5. Entity Authority Score — `EAS-1`

```
EAS = 100 * Σ_i (w_i * association_i)
```

Components: co_occurrence, semantic_proximity, ownership_signal, citation_linkage, topical_centrality, recency, cross_source_consistency.

Default weights: `0.20, 0.16, 0.18, 0.12, 0.12, 0.10, 0.12`.

### 6. Answer Readiness Score — `ARS-1`

```
ARS = 100 * (0.25*direct_answer_clarity + 0.20*evidence_density
           + 0.20*structure_for_extraction + 0.20*entity_clarity
           + 0.15*freshness_signal)
```

Inputs normalised 0–1 before weighting.

### 7. Generative Citability Score — `GCS-1`

```
GCS = mean(specificity, evidence, direct_answers, original_information,
           entity_clarity, source_attribution, freshness,
           structured_information, tables, definitions, comparisons)
```

Equal-weight mean of eleven components (0–100).

### 8. Content Moat Score — `CMS-1`

```
CMS = clamp100(format_prior + 0.12 * (information_gain_score - 50))
```

Example format priors: generic_listicle `18`, expert_interview `51`, original_dataset `86`, proprietary_benchmark_study `94`.

### 9. Topic Opportunity Score — `TOS-1`

```
TOS = 0.25*impact + 0.20*urgency + 0.15*confidence
    + 0.30*expected_value + 0.10*(100 - difficulty)
```

Difficulty is inverted so lower difficulty raises the score.

### 10. Writer Match Score — `WMS-1`

```
WMS = 0.28*dna_fit + 0.22*topic_fit + 0.18*client_fit
    + 0.12*audience_fit + 0.20*historical_outcome
```

**Similarity-only matching is rejected.**

### 11. Agent Readiness Score — `AGRS-1`

```
AGRS = Σ_i (w_i * check_score_i) / Σ_i w_i
```

Weighted average of agentic readiness checks (0–100). Proprietary Peacock surface — not an industry-standard claim.

### 12. Competitive Threat Score — `CTS-1`

```
CTS = 100 * (0.30*citation_share_gap + 0.25*soa_gap
           + 0.20*content_velocity + 0.15*entity_coverage_gap
           + 0.10*recent_acceleration)
```

Each factor normalised 0–1. Higher = greater threat.

### 13. Opportunity Confidence — `OC-1`

```
OC = clamp01(0.40*evidence_coverage + 0.30*signal_agreement
           + 0.20*data_recency + 0.10*sample_adequacy)
```

Unit `0–1`. Confidence in a recommendation — not a guaranteed win probability.

---

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/proprietary-metrics/catalog` | All formulas + weights + disclaimer |
| `GET` | `/proprietary-metrics/preview` | Demo scorecard |
| `POST` | `/proprietary-metrics/scorecards` | Persist scorecard |
| `GET` | `/proprietary-metrics/scorecards/{id}` | Retrieve scorecard |

## Tables

`proprietary_metric_scorecards`, `pm_metric_scores`, `pm_metric_components`
