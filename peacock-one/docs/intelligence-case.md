# PINE IntelligenceCase

Strongly typed aggregate used by Peacock Intelligence (PINE).

Persistence is **relational** — one root table plus typed child tables.
Collections are never stuffed into a monolithic JSON blob.

## Runtime contract

`services/intelligence/case.py` → `IntelligenceCase`

| Field | Notes |
| --- | --- |
| `case_id` | UUID |
| `organization_id` / `organisation_id` | Alias pair; British spelling is canonical in DB |
| `workspace_id` | Tenant workspace |
| `objective` | Case goal |
| `context` | Typed `CaseContextItem[]` |
| `observations` | Typed `CaseObservation[]` |
| `evidence` | Typed `CaseEvidence[]` with scalar value columns |
| `hypotheses` | Typed `CaseHypothesis[]` |
| `agent_findings` | Typed `CaseAgentFinding[]` (+ claim rows) |
| `contradictions` | Typed `CaseContradiction[]` |
| `unknowns` | Typed `CaseUnknown[]` |
| `assumptions` | Typed `CaseAssumption[]` |
| `risks` | Typed `CaseRisk[]` |
| `opportunities` | Typed `CaseOpportunity[]` |
| `recommendations` | Typed `CaseRecommendation[]` (+ evidence refs) |
| `confidence` | Aggregate confidence 0–1 |
| `models_used` | Typed `CaseModelUsed[]` |
| `tools_used` | Typed `CaseToolUsed[]` |
| `cost` / `latency` | `cost_usd_micros`, `latency_ms` |
| `created_at` | Timestamp |

## Relational tables

| Table | Role |
| --- | --- |
| `intelligence_cases` | Root aggregate (`IntelligenceCaseRecord`) |
| `intelligence_case_context_items` | Selected context slices |
| `intelligence_case_observations` | Observations |
| `intelligence_case_evidence` | Evidence with `value_text` / `value_number` / `value_bool` |
| `intelligence_case_evidence_urls` | Related URLs per evidence row |
| `intelligence_case_hypotheses` | Hypotheses |
| `intelligence_case_agent_findings` | Agent findings |
| `intelligence_case_agent_claims` | Claims under a finding |
| `intelligence_case_contradictions` | Adversarial contradictions |
| `intelligence_case_unknowns` | Open questions |
| `intelligence_case_assumptions` | Assumptions |
| `intelligence_case_risks` | Risks |
| `intelligence_case_opportunities` | Opportunities |
| `intelligence_case_recommendations` | Recommendations |
| `intelligence_case_recommendation_evidence` | Evidence code refs per recommendation |
| `intelligence_case_models_used` | Models invoked |
| `intelligence_case_tools_used` | Tools invoked |

Child rows CASCADE with the case. Tenant FKs denormalize `organisation_id` / `workspace_id`.

## API

- `POST /intelligence/cases` — upsert relational case
- `GET /intelligence/cases/{case_id}` — hydrate typed case

## Code

- ORM: `packages/db_models/intelligence_case.py`
- Typed object: `services/intelligence/case.py`
- Repository: `services/intelligence/case_repository.py`
- Migration: `database/migrations/versions/0006_pine_intelligence_case.py`
