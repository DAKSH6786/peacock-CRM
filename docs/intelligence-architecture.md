# Generative Visibility Intelligence Architecture

## Non-goals

- Prompt fan-out to all LLMs with identical instructions
- Treating model prose as ground truth
- Skipping deterministic crawl / audit / probe evidence

## Layered stack

```text
┌──────────────────────────────────────────────────────────┐
│  Surfaces: Intelligence Cockpit, Strategy, Monitoring    │
├──────────────────────────────────────────────────────────┤
│  Cognitive Pipeline Orchestrator (OBSERVE…LEARN)         │
├──────────────┬───────────────┬───────────────────────────┤
│ Domain engines│ Knowledge     │ Decision & Learning       │
│ SEO / AEO /   │ Entities + KG │ Scoring, policies,        │
│ GEO / Crawl / │ Competitor    │ recommendation weights    │
│ Visibility    │ Keyword graph │ Outcome attribution       │
├──────────────┴───────────────┴───────────────────────────┤
│  Connector fabric (role-bound providers)                 │
│  OpenAI · Gemini · Claude · Perplexity · DeepSeek        │
├──────────────────────────────────────────────────────────┤
│  Jobs · Storage · Postgres · Audit · Permissions         │
└──────────────────────────────────────────────────────────┘
```

## Connector roles (multi-layer reasoning)

| Provider       | Default roles                                                  | Why                                          |
| -------------- | -------------------------------------------------------------- | -------------------------------------------- |
| **Perplexity** | `WEB_RESEARCH`, `CITATION_HUNT`                                | Live web grounding & source discovery        |
| **Claude**     | `STRUCTURAL_CRITIQUE`, `CONTENT_QUALITY`, `VERIFY_ADVERSARIAL` | Long-context critique & careful verification |
| **OpenAI**     | `SYNTHESIS`, `STRATEGY_FRAME`, `WRITER_BRIEF`                  | Planning & actionable packaging              |
| **Gemini**     | `ENTITY_EXTRACTION`, `MULTIMODAL_PAGE`, `KNOWLEDGE_LINK`       | Entities, schemas, page/structure signals    |
| **DeepSeek**   | `SECOND_OPINION`, `COST_SWEEP`, `VERIFY_CONSENSUS`             | Independent challenge & economical sweeps    |

Role assignment is explicit in `modules/connectors/roles.ts`. Pipeline stages request **roles**, never raw provider names. The registry resolves role → provider → prompt template.

## Stage contracts

### OBSERVE

Inputs: property URL, competitor set, keyword universe, prior run snapshot.

Outputs (structured only):

- Crawl graph + page inventory
- Technical SEO findings
- Content blocks & schema markup
- Keyword / backlink / competitor snapshots
- AI visibility probe raw answers (separate probe prompts)

### THINK

Inputs: OBSERVE artifacts only (plus org policy).

Runs specialist roles in parallel where independent, then a synthesis role that must cite artifact IDs.

### VERIFY

- Deterministic validators (URL exists, metric thresholds, schema validity)
- Adversarial LLM check against cited artifacts
- Cross-model consensus score; low consensus → flag, do not auto-execute

### DECIDE

Priority scoring combines:

- Impact estimate
- Confidence (evidence coverage × consensus)
- Effort / risk
- Org policy gates

### EXECUTE

Emits durable work products: content briefs, writer packs, technical tickets, 90-day strategy packs. No silent mutation of client sites.

### MEASURE

Scheduled visibility probes & outcome KPIs keyed to executed recommendations.

### LEARN

Outcome signals adjust recommendation model weights (`RecommendationWeight`). Learning never bypasses VERIFY on the next cycle.

## Run model

`IntelligenceRun` is the unit of work. Each stage writes `IntelligenceStageResult` with:

- `status`, `startedAt`, `completedAt`
- `artifactRefs` (IDs of observe/think objects)
- `confidence`
- `providerTraces` (role, provider, promptHash — not full secrets)

Failed VERIFY blocks EXECUTE unless an admin overrides with audit.

## Extensibility

Domain engines under `modules/{crawl,seo,aeo,geo,visibility,strategy,knowledge}` expose pure functions + services. The orchestrator in `modules/intelligence` is the only place that sequences the cognitive loop.
